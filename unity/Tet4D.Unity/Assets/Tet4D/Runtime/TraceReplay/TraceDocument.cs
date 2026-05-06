using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace Tet4D.UnityReplay.TraceReplay
{
    public sealed class TraceDocument
    {
        public JObject Root { get; private set; }
        public string TraceType { get; private set; }
        public string CaseId { get; private set; }
        public string CollisionMode { get; private set; }
        public string TopologyPreset { get; private set; }
        public string FinalStateHash { get; private set; }
        public int Dimension { get; private set; }
        public int[] BoardShape { get; private set; }
        public List<TraceFrame> Frames { get; private set; }

        public static TraceDocument FromJson(string jsonText)
        {
            JObject root = TraceJson.ParseObject(jsonText);
            JArray framesArray = TraceJson.GetArray(root, "frames");
            List<TraceFrame> frames = new List<TraceFrame>();
            if (framesArray != null)
            {
                foreach (JToken token in framesArray)
                {
                    frames.Add(TraceFrame.FromToken(token as JObject));
                }
            }

            int[] boardShape = TraceJson.GetIntArray(root, "board_shape");
            if (boardShape.Length == 0)
            {
                boardShape = TraceJson.GetIntArray(root.SelectToken("initial.axis_sizes") as JArray);
            }

            TraceDocument document = new TraceDocument();
            document.Root = root;
            document.TraceType = TraceJson.GetString(root, "trace_type");
            document.CaseId = TraceJson.GetString(root, "case_id");
            document.CollisionMode = TraceJson.GetString(root, "collision_mode");
            document.TopologyPreset = TraceJson.GetString(root, "topology_preset");
            document.FinalStateHash = TraceJson.GetString(root, "final.state_hash");
            document.Dimension = TraceJson.GetInt(root, "dimension");
            document.BoardShape = boardShape;
            document.Frames = frames;
            return document;
        }
    }
}
