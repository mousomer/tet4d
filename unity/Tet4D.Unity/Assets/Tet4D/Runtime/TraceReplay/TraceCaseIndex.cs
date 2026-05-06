using Newtonsoft.Json.Linq;

namespace Tet4D.UnityReplay.TraceReplay
{
    public sealed class TraceCaseIndex
    {
        public string TraceType { get; private set; }
        public string CaseId { get; private set; }
        public string RelativePath { get; private set; }
        public string SourcePath { get; private set; }
        public string Sha256 { get; private set; }
        public string TopologyId { get; private set; }
        public string TopologyPreset { get; private set; }
        public string FinalStateHash { get; private set; }
        public int Dimension { get; private set; }
        public int FrameCount { get; private set; }
        public int TraceVersion { get; private set; }

        public static TraceCaseIndex FromToken(string traceType, JToken token)
        {
            TraceCaseIndex index = new TraceCaseIndex();
            index.TraceType = TraceJson.GetString(token, "trace_type", traceType);
            index.CaseId = TraceJson.GetString(token, "case_id");
            index.RelativePath = TraceJson.GetString(token, "path");
            index.SourcePath = TraceJson.GetString(token, "source_path");
            index.Sha256 = TraceJson.GetString(token, "sha256");
            index.TopologyId = TraceJson.GetString(token, "topology_id");
            index.TopologyPreset = TraceJson.GetString(token, "topology_preset");
            index.FinalStateHash = TraceJson.GetString(token, "final_state_hash");
            index.Dimension = TraceJson.GetInt(token, "dimension");
            index.FrameCount = TraceJson.GetInt(token, "frame_count");
            index.TraceVersion = TraceJson.GetInt(token, "trace_version");
            return index;
        }
    }
}
