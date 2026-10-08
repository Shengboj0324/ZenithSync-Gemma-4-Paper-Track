package raft

import (
	"bytes"
	"errors"
	"io/ioutil"
	"strings"
	"testing"
	"time"
)

type shutdownSnapshotFSM struct {
	FSM
	snapshot FSMSnapshot
}

func (f *shutdownSnapshotFSM) Snapshot() (FSMSnapshot, error) {
	return f.snapshot, nil
}

type shutdownSnapshot struct {
	persistStarted  chan struct{}
	persistContinue chan struct{}
	released        chan struct{}
	persistErr      error
}

func (s *shutdownSnapshot) Persist(sink SnapshotSink) error {
	close(s.persistStarted)
	if s.persistContinue != nil {
		<-s.persistContinue
	}
	if s.persistErr != nil {
		return s.persistErr
	}
	if _, err := sink.Write([]byte("snapshot contents")); err != nil {
		return err
	}
	return sink.Close()
}

func (s *shutdownSnapshot) Release() {
	close(s.released)
}

// Start the real FSM and snapshot workers, but leave configuration responses
// under the test's control to reproduce the main worker exiting with a pending
// buffered request. No elections or timing-dependent scheduling are needed.
func newSnapshotShutdownRaft(t *testing.T, snap FSMSnapshot) *Raft {
	t.Helper()
	conf := inmemConfig(t)
	conf.LocalID = "snapshot-test"
	conf.SnapshotInterval = time.Hour
	conf.skipStartup = true
	store := NewInmemStore()
	_, trans := NewInmemTransport("")
	r, err := NewRaft(conf, &shutdownSnapshotFSM{FSM: &MockFSM{}, snapshot: snap},
		store, store, NewInmemSnapshotStore(), trans)
	if err != nil {
		t.Fatal(err)
	}
	r.goFunc(r.runFSM)
	apply := &logFuture{log: Log{Index: 2, Term: 1, Type: LogCommand, Data: []byte("command")}}
	apply.init()
	r.fsmMutateCh <- []*commitTuple{{log: &apply.log, future: apply}}
	if err := waitSnapshotFuture(t, apply); err != nil {
		t.Fatal(err)
	}
	r.goFunc(r.runSnapshots)
	return r
}

func waitSnapshotFuture(t *testing.T, future Future) error {
	t.Helper()
	done := make(chan error, 1)
	go func() { done <- future.Error() }()
	select {
	case err := <-done:
		return err
	case <-time.After(5 * time.Second):
		t.Fatal("future did not complete")
		return nil
	}
}

func waitSnapshotSignal(t *testing.T, signal <-chan struct{}) {
	t.Helper()
	select {
	case <-signal:
	case <-time.After(5 * time.Second):
		t.Fatal("snapshot worker did not reach expected stage")
	}
}

func snapshotConfigurationRequest(t *testing.T, r *Raft) *configurationsFuture {
	t.Helper()
	select {
	case req := <-r.configurationsCh:
		return req
	case <-time.After(5 * time.Second):
		t.Fatal("snapshot did not request configuration")
		return nil
	}
}

func TestRaft_SnapshotShutdownPendingConfiguration(t *testing.T) {
	snap := &shutdownSnapshot{persistStarted: make(chan struct{}), released: make(chan struct{})}
	r := newSnapshotShutdownRaft(t, snap)
	defer r.Shutdown()
	future := r.Snapshot()
	// The main worker may exit without responding to this buffered request.
	config := snapshotConfigurationRequest(t, r)
	// Unblock the worker on test failure, including when run against the old
	// implementation, so the regression does not leave a goroutine behind.
	defer config.respond(ErrRaftShutdown)
	shutdown := r.Shutdown()
	if err := waitSnapshotFuture(t, shutdown); err != nil {
		t.Fatalf("shutdown: %v", err)
	}
	if err := waitSnapshotFuture(t, future); err != ErrRaftShutdown {
		t.Fatalf("snapshot error = %v, want %v", err, ErrRaftShutdown)
	}
	waitSnapshotSignal(t, snap.released)
	select {
	case <-snap.persistStarted:
		t.Fatal("snapshot persisted without a configuration response")
	default:
	}
}

func TestRaft_SnapshotConfigurationError(t *testing.T) {
	snap := &shutdownSnapshot{persistStarted: make(chan struct{}), released: make(chan struct{})}
	r := newSnapshotShutdownRaft(t, snap)
	defer func() { waitSnapshotFuture(t, r.Shutdown()) }()
	future := r.Snapshot()
	snapshotConfigurationRequest(t, r).respond(ErrLeadershipTransferInProgress)
	if err := waitSnapshotFuture(t, future); err != ErrLeadershipTransferInProgress {
		t.Fatalf("snapshot error = %v, want %v", err, ErrLeadershipTransferInProgress)
	}
	waitSnapshotSignal(t, snap.released)
}

func TestRaft_SnapshotShutdownDuringPersist(t *testing.T) {
	for _, persistErr := range []error{nil, errors.New("snapshot storage failed")} {
		name := "success"
		if persistErr != nil {
			name = "error"
		}
		t.Run(name, func(t *testing.T) {
			snap := &shutdownSnapshot{
				persistStarted: make(chan struct{}), persistContinue: make(chan struct{}),
				released: make(chan struct{}), persistErr: persistErr,
			}
			r := newSnapshotShutdownRaft(t, snap)
			defer r.Shutdown()
			future := r.Snapshot()
			config := snapshotConfigurationRequest(t, r)
			config.configurations.committedIndex = 1
			config.respond(nil)
			waitSnapshotSignal(t, snap.persistStarted)
			shutdown := r.Shutdown()
			done := make(chan error, 1)
			go func() { done <- shutdown.Error() }()
			select {
			case <-done:
				t.Fatal("shutdown returned before snapshot persistence finished")
			case <-time.After(20 * time.Millisecond):
			}
			close(snap.persistContinue)
			err := waitSnapshotFuture(t, future)
			if persistErr != nil {
				if err == nil || !strings.Contains(err.Error(), persistErr.Error()) {
					t.Fatalf("snapshot error = %v, want persistence error %v", err, persistErr)
				}
			} else {
				if err != nil {
					t.Fatal(err)
				}
				meta, reader, err := future.Open()
				if err != nil {
					t.Fatal(err)
				}
				contents, err := ioutil.ReadAll(reader)
				reader.Close()
				if err != nil || !bytes.Equal(contents, []byte("snapshot contents")) || meta.Index != 2 {
					t.Fatalf("persisted snapshot: metadata=%+v contents=%q error=%v", meta, contents, err)
				}
			}
			waitSnapshotSignal(t, snap.released)
			select {
			case err := <-done:
				if err != nil {
					t.Fatal(err)
				}
			case <-time.After(5 * time.Second):
				t.Fatal("shutdown did not finish after persistence")
			}
		})
	}
}
