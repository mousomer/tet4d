using System.Collections.Generic;
using System.Text;
using Newtonsoft.Json.Linq;

namespace Tet4D.UnityReplay.TraceReplay
{
    public static class TraceSnapshotExtractor
    {
        public static TraceRenderSnapshot Extract(TraceDocument document, int frameIndex)
        {
            TraceRenderSnapshot snapshot = new TraceRenderSnapshot();
            snapshot.TraceType = document.TraceType;
            snapshot.CaseId = document.CaseId;
            snapshot.Dimension = document.Dimension;
            snapshot.FrameCount = document.Frames.Count;
            snapshot.FrameIndex = frameIndex;
            snapshot.BoardShape = document.BoardShape;

            if (frameIndex < 0 || frameIndex >= document.Frames.Count)
            {
                snapshot.MetadataText = "Frame out of range.";
                snapshot.DiagnosticsText = string.Empty;
                return snapshot;
            }

            TraceFrame frame = document.Frames[frameIndex];
            snapshot.StateHash = frame.StateHash;

            if (document.TraceType == "topology")
            {
                ExtractTopology(document, frame.Raw, snapshot);
            }
            else if (document.TraceType == "gameplay")
            {
                ExtractGameplay(document, frame.Raw, snapshot);
            }
            else if (document.TraceType == "endgame")
            {
                ExtractEndgame(document, frame.Raw, snapshot);
            }
            else
            {
                snapshot.MetadataText = "Unknown trace type.";
                snapshot.DiagnosticsText = TraceJson.ToSummary(frame.Raw);
            }

            return snapshot;
        }

        private static void ExtractTopology(
            TraceDocument document,
            JObject frame,
            TraceRenderSnapshot snapshot
        )
        {
            AddMarker(
                snapshot.ProbeMarkers,
                "probe_before",
                "Probe Before",
                TraceJson.GetFloatArray(frame.SelectToken("before.probe_coord") as JArray)
            );
            AddMarker(
                snapshot.ProbeMarkers,
                "probe_after",
                "Probe After",
                TraceJson.GetFloatArray(frame.SelectToken("after.probe_coord") as JArray)
            );

            JArray movedCells = TraceJson.GetArray(frame, "piece_transport.moved_cells");
            if (movedCells != null)
            {
                foreach (JToken cell in movedCells)
                {
                    snapshot.ActiveCells.Add(
                        new CellSnapshot
                        {
                            Label = "Transport",
                            ColorId = 1,
                            Position = TraceJson.GetFloatArray(cell as JArray),
                            IsLocked = false
                        }
                    );
                }
            }

            AddTraversalMarker(
                snapshot.EventMarkers,
                frame.SelectToken("probe_result.traversal") as JObject,
                frame.SelectToken("after.probe_coord") as JArray
            );

            snapshot.MetadataText = BuildMetadata(
                "Topology Replay",
                "command",
                TraceJson.GetString(frame, "command_id"),
                "legal",
                TraceJson.GetString(frame, "legal"),
                "state_hash",
                snapshot.StateHash
            );
            snapshot.DiagnosticsText = TraceJson.ToSummary(
                frame.SelectToken("diagnostics") ?? document.Root.SelectToken("initial.diagnostics")
            );
        }

        private static void ExtractGameplay(
            TraceDocument document,
            JObject frame,
            TraceRenderSnapshot snapshot
        )
        {
            JArray activeCells = TraceJson.GetArray(frame, "active_piece.cells");
            if (activeCells != null)
            {
                foreach (JToken cell in activeCells)
                {
                    snapshot.ActiveCells.Add(
                        new CellSnapshot
                        {
                            Label = "Active",
                            ColorId = TraceJson.GetInt(frame, "active_piece.color_id", 1),
                            Position = TraceJson.GetFloatArray(cell as JArray),
                            IsLocked = false
                        }
                    );
                }
            }

            JArray lockedCells = TraceJson.GetArray(frame, "locked_cells");
            if (lockedCells != null)
            {
                foreach (JToken cell in lockedCells)
                {
                    snapshot.LockedCells.Add(
                        new CellSnapshot
                        {
                            Label = "Locked",
                            ColorId = 0,
                            Position = TraceJson.GetFloatArray(cell as JArray),
                            IsLocked = true
                        }
                    );
                }
            }

            JArray traversals = TraceJson.GetArray(frame, "topology_event.traversals");
            if (traversals != null)
            {
                float[] eventPosition = FirstCellPosition(snapshot.ActiveCells);
                foreach (JToken traversal in traversals)
                {
                    AddTraversalMarker(
                        snapshot.EventMarkers,
                        traversal as JObject,
                        eventPosition
                    );
                }
            }

            snapshot.MetadataText = BuildMetadata(
                "Gameplay Replay",
                "command",
                TraceJson.GetString(frame, "command_id"),
                "score",
                TraceJson.GetString(frame, "score"),
                "lines",
                TraceJson.GetString(frame, "lines"),
                "locked",
                TraceJson.GetString(frame, "drop_lock_status.locked_cell_count"),
                "state_hash",
                snapshot.StateHash
            );
            snapshot.DiagnosticsText = TraceJson.ToSummary(frame.SelectToken("topology_event"));
        }

        private static void ExtractEndgame(
            TraceDocument document,
            JObject frame,
            TraceRenderSnapshot snapshot
        )
        {
            JArray particles = TraceJson.GetArray(frame, "particles");
            if (particles != null)
            {
                foreach (JToken particleToken in particles)
                {
                    ParticleSnapshot particle = new ParticleSnapshot();
                    particle.ColorId = TraceJson.GetInt(particleToken, "color_id");
                    particle.ParticleId = TraceJson.GetInt(particleToken, "particle_id");
                    particle.Active = TraceJson.GetBool(particleToken, "active", true);
                    particle.Escaped = TraceJson.GetBool(particleToken, "escaped", false);
                    particle.Mass = TraceJson.GetFloat(particleToken, "mass", 1f);
                    particle.Radius = TraceJson.GetFloat(particleToken, "radius", 0.25f);
                    particle.Position = TraceJson.GetFloatArray(particleToken, "position");
                    particle.Velocity = TraceJson.GetFloatArray(particleToken, "velocity");
                    particle.SourceCoord = TraceJson.GetIntArray(
                        particleToken.SelectToken("source_coord") as JArray
                    );
                    snapshot.Particles.Add(particle);
                }
            }

            JArray events = TraceJson.GetArray(frame, "events");
            if (events != null)
            {
                foreach (JToken eventToken in events)
                {
                    int particleId = TraceJson.GetInt(eventToken, "particle_id", -1);
                    float[] particlePosition = FindParticlePosition(snapshot.Particles, particleId);
                    AddMarker(
                        snapshot.EventMarkers,
                        TraceJson.GetString(eventToken, "kind", "event"),
                        TraceJson.ToSummary(eventToken, 120),
                        particlePosition
                    );
                }
            }

            snapshot.MetadataText = BuildMetadata(
                "Endgame Replay",
                "collision",
                document.CollisionMode,
                "energy",
                TraceJson.GetString(frame, "energy.kinetic_energy"),
                "particles",
                snapshot.Particles.Count.ToString(),
                "state_hash",
                snapshot.StateHash
            );
            snapshot.DiagnosticsText = TraceJson.ToSummary(
                frame.SelectToken("events") ?? frame.SelectToken("energy")
            );
        }

        private static void AddTraversalMarker(
            List<MarkerSnapshot> markers,
            JObject traversal,
            JArray referencePosition
        )
        {
            AddTraversalMarker(
                markers,
                traversal,
                TraceJson.GetFloatArray(referencePosition)
            );
        }

        private static void AddTraversalMarker(
            List<MarkerSnapshot> markers,
            JObject traversal,
            float[] referencePosition
        )
        {
            if (traversal == null || referencePosition == null || referencePosition.Length == 0)
            {
                return;
            }

            AddMarker(
                markers,
                "seam",
                TraceJson.ToSummary(traversal, 120),
                referencePosition
            );
        }

        private static void AddMarker(
            List<MarkerSnapshot> markers,
            string kind,
            string label,
            float[] position
        )
        {
            if (position == null || position.Length == 0)
            {
                return;
            }

            markers.Add(
                new MarkerSnapshot
                {
                    Kind = kind,
                    Label = label,
                    Position = position
                }
            );
        }

        private static string BuildMetadata(string title, params string[] keyValues)
        {
            StringBuilder builder = new StringBuilder();
            builder.AppendLine(title);
            for (int index = 0; index + 1 < keyValues.Length; index += 2)
            {
                builder.Append(keyValues[index]);
                builder.Append(": ");
                builder.AppendLine(keyValues[index + 1]);
            }

            return builder.ToString().TrimEnd();
        }

        private static float[] FirstCellPosition(List<CellSnapshot> cells)
        {
            if (cells.Count == 0)
            {
                return null;
            }

            return cells[0].Position;
        }

        private static float[] FindParticlePosition(List<ParticleSnapshot> particles, int particleId)
        {
            foreach (ParticleSnapshot particle in particles)
            {
                if (particle.ParticleId == particleId)
                {
                    return particle.Position;
                }
            }

            return null;
        }
    }
}
