namespace Tet4D.UnityReplay.TraceReplay
{
    public sealed class TracePlaybackState
    {
        public int CurrentFrameIndex;
        public float PlaybackSpeed = 4f;
        public bool IsPlaying;
        public bool DiagnosticsVisible = true;

        public void Reset()
        {
            CurrentFrameIndex = 0;
            IsPlaying = false;
        }
    }
}
