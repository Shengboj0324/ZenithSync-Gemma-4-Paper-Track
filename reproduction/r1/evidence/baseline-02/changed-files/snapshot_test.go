package raft

import (
	"errors"
	"io/ioutil"
	"testing"
	"time"
)

type shutdownSnapshotFSM struct {
	MockFSM
	snapshot FSMSnapshot
}

func (f *shutdownSnapshotFSM) Snapshot() (FSMSnapshot, error) {
	return f.snapshot, nil
}

type shutdownTestSnapshot struct {
	entered  chan struct{}
	proceed  chan struct{}
	released chan struct{}
	err      error
}

func (s *shutdownTestSnapshot) Persist(sink SnapshotSink) error {
	close(s.entered)
	<-s.proceed
	if s.err != nil {
		return s.err
	}
	if _, err := sink.Write([]byte("snapshot data")); err != nil {
		return err
	}
	return sink.Close()
}

func (s *shutdownTestSnapshot) Release() {
	close(s.released)
}

// Start the real FSM and snapshot workers, but leave configuration requests
// queued as they would be if the main Raft worker had already exited.
func newShutdownSnapshotRaft(t *testing.T, snapshot FSMSnapshot) *Raft {
	t.Helper()
	conf := inmemConfig(t)
	conf.LocalID = "snapshot-test"
	conf.SnapshotInterval = time.Hour
	conf.skipStartup = true
	_, transport := NewInmemTransport("snapshot-test")
	store := NewInmemStore()
	r, err := NewRaft(conf, &shutdownSnapshotFSM{snapshot: snapshot}, store, store,
		NewInmemSnapshotStore(), transport)
	if err != nil {
		t.Fatal(err)
	}
	r.goFunc(r.runFSM)
	apply := &logFuture{}
	apply.init()
	r.fsmMutateCh <- []*commitTuple{{
		log:    &Log{Index: 1, Term: 1, Type: LogCommand, Data: []byte("command")},
		future: apply,
	}}
	if err := apply.Error(); err != nil {
		t.Fatal(err)
	}
	r.setLastLog(1, 1)
	r.goFunc(r.runSnapshots)
	return r
}

func snapshotFutureResult(f Future) <-chan error {
	result := make(chan error, 1)
	go func() { result <- f.Error() }()
	return result
}

func waitSnapshotResult(t *testing.T, result <-chan error) error {
	t.Helper()
	select {
	case err := <-result:
		return err
	case <-time.After(5 * time.Second):
		t.Fatal("timed out waiting for future")
		return nil
	}
}

func TestRaft_SnapshotShutdownWaitingForConfiguration(t *testing.T) {
	for _, shutdown := range []bool{true, false} {
		name := "configuration-error"
		if shutdown {
			name = "shutdown"
		}
		t.Run(name, func(t *testing.T) {
			snapshot := &shutdownTestSnapshot{
				entered: make(chan struct{}), released: make(chan struct{}),
			}
			r := newShutdownSnapshotRaft(t, snapshot)
			defer func() {
				r.Shutdown()
				r.waitShutdown()
			}()
			future := r.Snapshot()
			var req *configurationsFuture
			select {
			case req = <-r.configurationsCh:
			case <-time.After(5 * time.Second):
				t.Fatal("snapshot did not request configuration")
			}
			// Unblock the original implementation on failure so the regression
			// test does not leave its workers behind.
			defer req.respond(ErrRaftShutdown)
			want := ErrRaftShutdown
			if shutdown {
				if err := waitSnapshotResult(t, snapshotFutureResult(r.Shutdown())); err != nil {
					t.Fatalf("shutdown failed: %v", err)
				}
			} else {
				want = errors.New("configuration unavailable")
				req.respond(want)
			}
			if err := waitSnapshotResult(t, snapshotFutureResult(future)); err != want {
				t.Fatalf("snapshot error = %v, want %v", err, want)
			}
			select {
			case <-snapshot.released:
			default:
				t.Fatal("snapshot was not released")
			}
			select {
			case <-snapshot.entered:
				t.Fatal("snapshot persisted without configuration")
			default:
			}
			if _, _, err := future.Open(); err == nil {
				t.Fatal("failed snapshot should not be available to open")
			}
		})
	}
}

func TestRaft_SnapshotShutdownDuringPersist(t *testing.T) {
	for _, fail := range []bool{false, true} {
		name := "success"
		if fail {
			name = "persist-error"
		}
		t.Run(name, func(t *testing.T) {
			snapshot := &shutdownTestSnapshot{
				entered: make(chan struct{}), proceed: make(chan struct{}), released: make(chan struct{}),
			}
			if fail {
				snapshot.err = errors.New("storage unavailable")
			}
			r := newShutdownSnapshotRaft(t, snapshot)
			defer func() {
				r.Shutdown()
				r.waitShutdown()
			}()
			// Always let persistence finish, including on assertion failure.
			defer func() {
				select {
				case <-snapshot.proceed:
				default:
					close(snapshot.proceed)
				}
			}()
			future := r.Snapshot()
			select {
			case req := <-r.configurationsCh:
				req.respond(nil)
			case <-time.After(5 * time.Second):
				t.Fatal("snapshot did not request configuration")
			}
			select {
			case <-snapshot.entered:
			case <-time.After(5 * time.Second):
				t.Fatal("snapshot did not start persistence")
			}
			shutdown := snapshotFutureResult(r.Shutdown())
			select {
			case err := <-shutdown:
				t.Fatalf("shutdown returned before persistence finished: %v", err)
			case <-time.After(50 * time.Millisecond):
			}
			close(snapshot.proceed)
			if err := waitSnapshotResult(t, shutdown); err != nil {
				t.Fatalf("shutdown failed: %v", err)
			}
			err := waitSnapshotResult(t, snapshotFutureResult(future))
			if fail {
				if err == nil || err.Error() != "failed to persist snapshot: storage unavailable" {
					t.Fatalf("unexpected persistence error: %v", err)
				}
			} else {
				if err != nil {
					t.Fatal(err)
				}
				meta, reader, err := future.Open()
				if err != nil {
					t.Fatal(err)
				}
				defer reader.Close()
				data, err := ioutil.ReadAll(reader)
				if err != nil || string(data) != "snapshot data" || meta.Index != 1 || meta.Term != 1 {
					t.Fatalf("invalid persisted snapshot: meta=%+v, data=%q, error=%v", meta, data, err)
				}
			}
			select {
			case <-snapshot.released:
			default:
				t.Fatal("snapshot was not released")
			}
		})
	}
}
