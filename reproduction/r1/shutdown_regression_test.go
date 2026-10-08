package raft

import (
	"bytes"
	"io/ioutil"
	"runtime"
	"testing"
	"time"

	"github.com/hashicorp/go-hclog"
)

// This component fixture runs the upstream snapshot worker and Shutdown API.
// A controlled peer models the main worker accepting no more requests. It is
// not a full cluster or a reproduction of the original dqlite deployment.
func r1SnapshotFixture() *Raft {
	conf := DefaultConfig()
	conf.SnapshotInterval = time.Hour
	r := &Raft{
		conf:             *conf,
		protocolVersion:  conf.ProtocolVersion,
		shutdownCh:       make(chan struct{}),
		fsmSnapshotCh:    make(chan *reqSnapshotFuture),
		configurationsCh: make(chan *configurationsFuture, 8),
		userSnapshotCh:   make(chan *userSnapshotFuture),
		logger:           hclog.New(&hclog.LoggerOptions{Output: ioutil.Discard}),
		logs:             NewInmemStore(),
		snapshots:        NewInmemSnapshotStore(),
	}
	r.goFunc(r.runSnapshots)
	return r
}

func r1StartSnapshot(t *testing.T, r *Raft) SnapshotFuture {
	t.Helper()
	future := r.Snapshot()
	select {
	case req := <-r.fsmSnapshotCh:
		req.index = 10
		req.term = 1
		req.snapshot = &MockSnapshot{logs: [][]byte{[]byte("retained")}, maxIndex: 1}
		req.respond(nil)
	case <-time.After(2 * time.Second):
		t.Fatal("fixture: snapshot worker did not request FSM snapshot")
	}
	return future
}

func r1AwaitQueuedConfig(t *testing.T, r *Raft) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for len(r.configurationsCh) == 0 {
		if time.Now().After(deadline) {
			t.Fatal("fixture: configuration request never queued")
		}
		runtime.Gosched()
	}
}

func TestR1ShutdownWithPendingSnapshot(t *testing.T) {
	r := r1SnapshotFixture()
	future := r1StartSnapshot(t, r)
	r1AwaitQueuedConfig(t, r)
	// The send completed before shutdown. No main-worker response is possible
	// after its exit; closing shutdown must therefore release the waiter.
	shutdown := r.Shutdown()
	done := make(chan error, 1)
	go func() { done <- shutdown.Error() }()
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("shutdown returned %v", err)
		}
		if err := future.Error(); err != ErrRaftShutdown {
			t.Fatalf("snapshot error = %v, want ErrRaftShutdown", err)
		}
	case <-time.After(250 * time.Millisecond):
		// Release the deliberately unserviced request for clean test teardown.
		// This response happens only after the measured failure is established.
		req := <-r.configurationsCh
		req.respond(ErrRaftShutdown)
		select {
		case <-done:
		case <-time.After(2 * time.Second):
			t.Fatal("fixture cleanup failed after shutdown deadlock")
		}
		t.Fatal("R1_LIVENESS_FAILURE: shutdown waited for an abandoned snapshot request")
	}
}

func TestR1NormalSnapshotPreservesData(t *testing.T) {
	r := r1SnapshotFixture()
	defer func() {
		done := make(chan error, 1)
		go func() { done <- r.Shutdown().Error() }()
		select {
		case <-done:
		case <-time.After(2 * time.Second):
			t.Error("normal snapshot cleanup hung")
		}
	}()
	future := r1StartSnapshot(t, r)
	r1AwaitQueuedConfig(t, r)
	req := <-r.configurationsCh
	req.configurations = configurations{committedIndex: 1}
	req.respond(nil)
	done := make(chan error, 1)
	go func() { done <- future.Error() }()
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("normal snapshot returned %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("normal snapshot hung")
	}
	_, reader, err := future.Open()
	if err != nil {
		t.Fatal(err)
	}
	defer reader.Close()
	data, err := ioutil.ReadAll(reader)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Contains(data, []byte("retained")) {
		t.Fatal("snapshot did not persist original FSM data")
	}
}

func TestR1SnapshotAfterShutdown(t *testing.T) {
	r := r1SnapshotFixture()
	if err := r.Shutdown().Error(); err != nil {
		t.Fatal(err)
	}
	if err := r.Snapshot().Error(); err != ErrRaftShutdown {
		t.Fatalf("snapshot after shutdown = %v, want ErrRaftShutdown", err)
	}
}
