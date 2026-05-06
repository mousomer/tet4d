using Newtonsoft.Json.Linq;

namespace Tet4D.UnityReplay.TraceReplay
{
    public sealed class TraceFrame
    {
        public JObject Raw { get; private set; }
        public int FrameIndex { get; private set; }
        public string StateHash { get; private set; }

        public static TraceFrame FromToken(JObject token)
        {
            TraceFrame frame = new TraceFrame();
            frame.Raw = token ?? new JObject();
            frame.FrameIndex = TraceJson.GetInt(frame.Raw, "frame_index");
            frame.StateHash = TraceJson.GetString(frame.Raw, "state_hash");
            return frame;
        }
    }
}
