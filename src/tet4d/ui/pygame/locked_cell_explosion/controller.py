from __future__ import annotations

from dataclasses import dataclass, field

from .audio import aggregate_audio_events
from .model import ExplosionAudioState, ExplosionParticle, StandaloneExplosionConfig
from .render import render_particles
from .simulation import build_simulation, step_simulation
from .topology import ExplosionTopologyAdapter


@dataclass
class LockedCellExplosionController:
    config: StandaloneExplosionConfig
    simulation: object
    topology: ExplosionTopologyAdapter
    audio_state: ExplosionAudioState = field(default_factory=ExplosionAudioState)
    pending_audio_events: tuple[str, ...] = ()

    @property
    def particles(self) -> tuple[ExplosionParticle, ...]:
        return tuple(self.simulation.particles)

    @property
    def elapsed_ms(self) -> float:
        return float(self.simulation.elapsed_ms)

    @property
    def total_kinetic_energy(self) -> float:
        return float(self.simulation.total_kinetic_energy)

    def step(self, dt_ms: float) -> tuple[str, ...]:
        raw_events = step_simulation(
            self.simulation,
            adapter=self.topology,
            dt_ms=dt_ms,
            time_scale=float(self.config.time_scale),
        )
        self.pending_audio_events = aggregate_audio_events(
            raw_events,
            elapsed_ms=float(self.simulation.elapsed_ms),
            sound_enabled=bool(self.config.sound_enabled),
            state=self.audio_state,
        )
        return self.pending_audio_events

    def consume_audio_events(self) -> tuple[str, ...]:
        events = tuple(self.pending_audio_events)
        self.pending_audio_events = ()
        return events

    def render_particles(self, *, render_context) -> tuple[object, ...]:
        return render_particles(
            self.particles,
            dimension=int(self.config.dimension),
            board_dims=tuple(int(value) for value in self.config.topology.board_dims),
            render_context=render_context,
        )


def build_locked_cell_explosion(
    config: StandaloneExplosionConfig,
) -> LockedCellExplosionController:
    simulation, topology = build_simulation(config)
    return LockedCellExplosionController(
        config=config,
        simulation=simulation,
        topology=topology,
    )
