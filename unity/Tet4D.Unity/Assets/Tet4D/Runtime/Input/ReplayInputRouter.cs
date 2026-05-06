using Tet4D.UnityReplay.TraceReplay;
using UnityEngine;

namespace Tet4D.UnityReplay.Input
{
    internal static class ReplayInputRouter
    {
        public static void Poll(TraceReplayController controller)
        {
            if (controller == null || !controller.HasLoadedCase)
            {
                return;
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.LeftArrow))
            {
                controller.StepFrame(-1);
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.RightArrow))
            {
                controller.StepFrame(1);
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.Space))
            {
                controller.TogglePlayback();
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.R))
            {
                controller.ResetPlayback();
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.Alpha1))
            {
                controller.SelectTraceType("topology");
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.Alpha2))
            {
                controller.SelectTraceType("gameplay");
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.Alpha3))
            {
                controller.SelectTraceType("endgame");
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.UpArrow))
            {
                controller.SelectCaseRelative(-1);
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.DownArrow))
            {
                controller.SelectCaseRelative(1);
            }
        }
    }
}
