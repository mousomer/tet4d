using System.Collections.Generic;

namespace Tet4D.UnityReplay.TraceReplay
{
    public sealed class TraceRenderSnapshot
    {
        public string TraceType;
        public string CaseId;
        public string StateHash;
        public string MetadataText;
        public string DiagnosticsText;
        public int Dimension;
        public int FrameIndex;
        public int FrameCount;
        public int[] BoardShape;
        public readonly List<CellSnapshot> ActiveCells = new List<CellSnapshot>();
        public readonly List<CellSnapshot> LockedCells = new List<CellSnapshot>();
        public readonly List<MarkerSnapshot> ProbeMarkers = new List<MarkerSnapshot>();
        public readonly List<MarkerSnapshot> EventMarkers = new List<MarkerSnapshot>();
        public readonly List<ParticleSnapshot> Particles = new List<ParticleSnapshot>();
    }

    public sealed class CellSnapshot
    {
        public string Label;
        public int ColorId;
        public float[] Position;
        public bool IsLocked;
    }

    public sealed class MarkerSnapshot
    {
        public string Kind;
        public string Label;
        public float[] Position;
    }

    public sealed class ParticleSnapshot
    {
        public int ColorId;
        public int ParticleId;
        public bool Active;
        public bool Escaped;
        public float Mass;
        public float Radius;
        public float[] Position;
        public float[] Velocity;
        public int[] SourceCoord;
    }
}
