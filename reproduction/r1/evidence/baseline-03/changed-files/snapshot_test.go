package raft

import (
	"bytes"
	"errors"
	"testing"
	"time"
)

type shutdownSnapshot struct {
	FSMSnapshot
	persistStarted chan struct{}
	persistAllowed chan struct{}
	released       chan struct{}
	persistErr     error
}

func (s *shutdownSnapshot) Persist(sink SnapshotSink) error {
	close(s.persistStarted)
	<-s.persistAllowed
	if s.persistErr != nil {
		return s.persistErr
	}
	return s.FSMSnapshot.Persist(sink)
}

func (s *shutdownSnapshot) Release() {
	s.FSMSnapshot.Release()
	close(s.released)
}

type shutdownSnapshotFSM struct {
	MockFSM
	snapshot *shutdownSnapshot
}

func (f *shutdownSnapshotFSM) Snapshot() (FSMSnapshot, error) {
	snapshot, err := f.MockFSM.Snapshot()
	if err != nil {
		return nil, err
	}
	f.snapshot.FSMSnapshot = snapshot
	return f.snapshot, nil
}

// Run the real FSM and snapshot workers, but let the test control configuration
// responses to reproduce a main worker exiting with an unanswered request.
func newSnapshotShutdownTestRaft(t *testing.T) (*Raft, *shutdownSnapshot) {
	t.Helper()
	conf := DefaultConfig()
	conf.SnapshotInterval = time.Hour
	conf.TrailingLogs = 0
	snapshot := &shutdownSnapshot{
		persistStarted: make(chan struct{}),
		persistAllowed: make(chan struct{}),
		released:       make(chan struct{}),
	}
	_, trans := NewInmemTransport("snapshot-test")
	r := &Raft{
		conf:             *conf,
		protocolVersion:  conf.ProtocolVersion,
		fsm:              &shutdownSnapshotFSM{snapshot: snapshot},
		fsmMutateCh:      make(chan interface{}),
		fsmSnapshotCh:    make(chan *reqSnapshotFuture),
		configurationsCh: make(chan *configurationsFuture, 8),
		userSnapshotCh:   make(chan *userSnapshotFuture),
		shutdownCh:       make(chan struct{}),
		logger:           newTestLogger(t),
		logs:             NewInmemStore(),
		snapshots:        NewInmemSnapshotStore(),
		trans:            trans,
	}
	log := &Log{Index: 1, Term: 1, Type: LogCommand, Data: []byte("snapshot data")}
	if err := r.logs.StoreLog(log); err != nil {
		t.Fatal(err)
	}
	r.setLastLog(log.Index, log.Term)
	r.goFunc(r.runFSM)
	r.goFunc(r.runSnapshots)
	future := &logFuture{}
	future.init()
	r.fsmMutateCh <- []*commitTuple{{log: log, future: future}}
	if err := future.Error(); err != nil {
		t.Fatal(err)
	}
	return r, snapshot
}

func snapshotTestFutureError(t *testing.T, future Future) error {
	t.Helper()
	result := make(chan error, 1)
	go func() { result <- future.Error() }()
	select {
	case err := <-result:
		return err
	case <-time.After(2 * time.Second):
		t.Fatal("future did not complete")
		return nil
	}
}

func snapshotTestConfigurationRequest(t *testing.T, r *Raft) *configurationsFuture {
	t.Helper()
	select {
	case req := <-r.configurationsCh:
		return req
	case <-time.After(2 * time.Second):
		t.Fatal("snapshot did not request configuration")
		return nil
	}
}

func TestRaft_SnapshotShutdownPendingConfiguration(t *testing.T) {
	r, snapshot := newSnapshotShutdownTestRaft(t)
	future := r.Snapshot()
	configReq := snapshotTestConfigurationRequest(t, r)
	defer func() {
		// Also unblock the original implementation when the regression fails.
		configReq.respond(ErrRaftShutdown)
		r.Shutdown().Error()
		r.waitShutdown()
	}()

	// Dispatch succeeded, but the main worker never responds to the request.
	if err := snapshotTestFutureError(t, r.Shutdown()); err != nil {
		t.Fatalf("shutdown failed: %v", err)
	}
	if err := snapshotTestFutureError(t, future); err != ErrRaftShutdown {
		t.Fatalf("snapshot error = %v, want %v", err, ErrRaftShutdown)
	}
	if err := future.Error(); err != ErrRaftShutdown {
		t.Fatalf("repeated snapshot error = %v, want %v", err, ErrRaftShutdown)
	}
	select {
	case <-snapshot.released:
	default:
		t.Fatal("snapshot was not released")
	}
	select {
	case <-snapshot.persistStarted:
		t.Fatal("snapshot persisted without a configuration response")
	default:
	}
}

func TestRaft_SnapshotConfigurationError(t *testing.T) {
	r, snapshot := newSnapshotShutdownTestRaft(t)
	defer func() { r.Shutdown().Error() }()
	future := r.Snapshot()
	configReq := snapshotTestConfigurationRequest(t, r)
	want := errors.New("configuration unavailable")
	configReq.respond(want)
	if err := snapshotTestFutureError(t, future); err != want {
		t.Fatalf("snapshot error = %v, want %v", err, want)
	}
	select {
	case <-snapshot.released:
	default:
		t.Fatal("snapshot was not released after configuration error")
	}
}

func TestRaft_SnapshotShutdownDuringPersist(t *testing.T) {
	for _, fail := range []bool{false, true} {
		name := "success"
		if fail {
			name = "error"
		}
		t.Run(name, func(t *testing.T) {
			r, snapshot := newSnapshotShutdownTestRaft(t)
			if fail {
				snapshot.persistErr = errors.New("storage failure")
			}
			allowed := false
			defer func() {
				if !allowed {
					close(snapshot.persistAllowed)
				}
				r.Shutdown().Error()
				r.waitShutdown()
			}()
			future := r.Snapshot()
			configReq := snapshotTestConfigurationRequest(t, r)
			configReq.configurations.committedIndex = 1
			configReq.respond(nil)
			select {
			case <-snapshot.persistStarted:
			case <-time.After(2 * time.Second):
				t.Fatal("snapshot did not start persistence")
			}

			shutdown := r.Shutdown()
			shutdownResult := make(chan error, 1)
			go func() { shutdownResult <- shutdown.Error() }()
			select {
			case err := <-shutdownResult:
				t.Fatalf("shutdown returned before persistence completed: %v", err)
			case <-time.After(20 * time.Millisecond):
			}
			close(snapshot.persistAllowed)
			allowed = true
			select {
			case err := <-shutdownResult:
				if err != nil {
					t.Fatalf("shutdown failed: %v", err)
				}
			case <-time.After(2 * time.Second):
				t.Fatal("shutdown did not complete after persistence")
			}
			err := snapshotTestFutureError(t, future)
			if fail {
				if err == nil || err.Error() != "failed to persist snapshot: storage failure" {
					t.Fatalf("snapshot lost persistence error: %v", err)
				}
			} else {
				if err != nil {
					t.Fatalf("snapshot failed: %v", err)
				}
				meta, source, err := future.Open()
				if err != nil {
					t.Fatal(err)
				}
				restored := &MockFSM{}
				if err := restored.Restore(source); err != nil {
					t.Fatal(err)
				}
				if meta.Index != 1 || len(restored.logs) != 1 || !bytes.Equal(restored.logs[0], []byte("snapshot data")) {
					t.Fatalf("unexpected persisted snapshot: metadata=%+v, logs=%q", meta, restored.logs)
				}
				if first, err := r.logs.FirstIndex(); err != nil || first != 0 {
					t.Fatalf("logs were not compacted: first=%d, error=%v", first, err)
				}
			}
			select {
			case <-snapshot.released:
			default:
				t.Fatal("snapshot was not released after persistence")
			}
		})
	}
}
