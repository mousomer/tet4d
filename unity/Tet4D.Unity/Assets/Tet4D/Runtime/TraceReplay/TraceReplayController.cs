using System;
using System.Collections.Generic;
using Tet4D.UnityReplay.Input;
using Tet4D.UnityReplay.Rendering;
using Tet4D.UnityReplay.UI;
using UnityEngine;

namespace Tet4D.UnityReplay.TraceReplay
{
    public sealed class TraceReplayController : MonoBehaviour
    {
        [SerializeField] private string bundleFolderName = "tet4d_bundle";
        [SerializeField] private string initialTraceType = "topology";

        private TraceBundle bundle;
        private TraceDocument currentDocument;
        private TraceRenderSnapshot currentSnapshot;
        private readonly TracePlaybackState playback = new TracePlaybackState();
        private readonly List<string> currentCaseIds = new List<string>();
        private string currentTraceType;
        private string currentCaseId;
        private string statusMessage = "Bundle status: loading";
        private TraceSceneRenderer sceneRenderer;
        private ReplayHudController hudController;
        private CameraRigController cameraRig;

        public bool HasLoadedCase
        {
            get { return currentDocument != null; }
        }

        public bool IsPlaying
        {
            get { return playback.IsPlaying; }
        }

        public bool DiagnosticsVisible
        {
            get { return playback.DiagnosticsVisible; }
        }

        public float PlaybackSpeed
        {
            get { return playback.PlaybackSpeed; }
        }

        public string StatusMessage
        {
            get { return statusMessage; }
        }

        public string CurrentTraceType
        {
            get { return currentTraceType ?? string.Empty; }
        }

        public string CurrentCaseId
        {
            get { return currentCaseId ?? string.Empty; }
        }

        public IReadOnlyList<string> TraceTypes
        {
            get { return bundle != null ? bundle.TraceTypes() : new List<string>(); }
        }

        public IReadOnlyList<string> CurrentCaseIds
        {
            get { return currentCaseIds; }
        }

        public string FrameSummary
        {
            get
            {
                if (currentDocument == null)
                {
                    return "Frame 0 / 0";
                }

                return string.Format(
                    "Frame {0} / {1}\ncase_id: {2}\ntrace_type: {3}\ndimension: {4}\nstate_hash: {5}",
                    playback.CurrentFrameIndex,
                    Mathf.Max(currentDocument.Frames.Count - 1, 0),
                    currentDocument.CaseId,
                    currentDocument.TraceType,
                    currentDocument.Dimension,
                    currentSnapshot != null ? currentSnapshot.StateHash : string.Empty
                );
            }
        }

        public string MetadataText
        {
            get
            {
                return currentSnapshot != null
                    ? currentSnapshot.MetadataText
                    : "Metadata unavailable.";
            }
        }

        public string DiagnosticsText
        {
            get
            {
                return currentSnapshot != null
                    ? currentSnapshot.DiagnosticsText
                    : "Diagnostics unavailable.";
            }
        }

        private void Awake()
        {
            EnsureSceneServices();
        }

        private void Start()
        {
            LoadBundle();
        }

        private void Update()
        {
            ReplayInputRouter.Poll(this);
            if (currentDocument == null)
            {
                return;
            }

            if (playback.IsPlaying && currentDocument.Frames.Count > 0)
            {
                float framesAdvanced = playback.PlaybackSpeed * Time.deltaTime;
                if (framesAdvanced > 0f)
                {
                    int nextFrame = playback.CurrentFrameIndex + Mathf.Max(1, Mathf.FloorToInt(framesAdvanced));
                    if (nextFrame >= currentDocument.Frames.Count)
                    {
                        nextFrame = currentDocument.Frames.Count - 1;
                        playback.IsPlaying = false;
                    }

                    SetFrame(nextFrame);
                }
            }
        }

        public void StepFrame(int delta)
        {
            if (currentDocument == null)
            {
                return;
            }

            SetFrame(playback.CurrentFrameIndex + delta);
        }

        public void TogglePlayback()
        {
            if (currentDocument == null)
            {
                return;
            }

            playback.IsPlaying = !playback.IsPlaying;
        }

        public void ResetPlayback()
        {
            playback.Reset();
            RefreshSnapshot();
        }

        public void SetPlaybackSpeed(float speed)
        {
            playback.PlaybackSpeed = Mathf.Clamp(speed, 1f, 20f);
        }

        public void SetDiagnosticsVisible(bool visible)
        {
            playback.DiagnosticsVisible = visible;
        }

        public void SelectTraceType(string traceType)
        {
            if (bundle == null || string.IsNullOrEmpty(traceType))
            {
                return;
            }

            currentTraceType = traceType;
            currentCaseIds.Clear();
            List<TraceCaseIndex> cases = bundle.CasesForTraceType(traceType);
            foreach (TraceCaseIndex traceCase in cases)
            {
                currentCaseIds.Add(traceCase.CaseId);
            }

            if (currentCaseIds.Count == 0)
            {
                currentCaseId = string.Empty;
                currentDocument = null;
                currentSnapshot = null;
                statusMessage = "Bundle status: no cases for trace type " + traceType;
                return;
            }

            SelectCase(currentCaseIds[0]);
        }

        public void SelectCase(string caseId)
        {
            if (bundle == null || string.IsNullOrEmpty(caseId))
            {
                return;
            }

            List<TraceCaseIndex> cases = bundle.CasesForTraceType(currentTraceType);
            foreach (TraceCaseIndex traceCase in cases)
            {
                if (traceCase.CaseId != caseId)
                {
                    continue;
                }

                currentCaseId = caseId;
                currentDocument = TraceLoader.LoadCaseDocument(bundle, traceCase);
                playback.Reset();
                RefreshSnapshot();
                statusMessage = string.Format(
                    "Bundle status: loaded {0}/{1}",
                    currentTraceType,
                    caseId
                );
                return;
            }
        }

        public void SelectCaseRelative(int delta)
        {
            if (currentCaseIds.Count == 0)
            {
                return;
            }

            int currentIndex = currentCaseIds.IndexOf(currentCaseId);
            currentIndex = Mathf.Clamp(currentIndex + delta, 0, currentCaseIds.Count - 1);
            SelectCase(currentCaseIds[currentIndex]);
        }

        private void LoadBundle()
        {
            try
            {
                string bundleRoot = System.IO.Path.Combine(Application.streamingAssetsPath, bundleFolderName);
                bundle = TraceLoader.LoadBundle(bundleRoot);
                currentTraceType = bundle.CasesForTraceType(initialTraceType).Count > 0
                    ? initialTraceType
                    : bundle.TraceTypes()[0];
                statusMessage = string.Format(
                    "Bundle status: loaded manifest {0} ({1})",
                    bundle.Manifest.BundleType,
                    bundle.Manifest.ConfigCombinedDigest
                );
                SelectTraceType(currentTraceType);
            }
            catch (Exception exception)
            {
                statusMessage = "Bundle status: load failed\n" + exception.Message;
                Debug.LogException(exception);
            }
        }

        private void SetFrame(int frameIndex)
        {
            if (currentDocument == null)
            {
                return;
            }

            playback.CurrentFrameIndex = Mathf.Clamp(frameIndex, 0, currentDocument.Frames.Count - 1);
            RefreshSnapshot();
        }

        private void RefreshSnapshot()
        {
            if (currentDocument == null)
            {
                currentSnapshot = null;
                return;
            }

            currentSnapshot = TraceSnapshotExtractor.Extract(currentDocument, playback.CurrentFrameIndex);
            if (sceneRenderer != null)
            {
                sceneRenderer.Render(currentSnapshot);
            }

            if (cameraRig != null && currentSnapshot.BoardShape != null)
            {
                cameraRig.FrameBoard(
                    currentSnapshot.BoardShape,
                    currentSnapshot.Dimension,
                    sceneRenderer != null ? sceneRenderer.CurrentSliceStride : 6f
                );
            }
        }

        private void EnsureSceneServices()
        {
            sceneRenderer = FindObjectOfType<TraceSceneRenderer>();
            if (sceneRenderer == null)
            {
                GameObject rendererObject = new GameObject("TraceSceneRenderer");
                sceneRenderer = rendererObject.AddComponent<TraceSceneRenderer>();
            }

            cameraRig = FindObjectOfType<CameraRigController>();
            if (cameraRig == null)
            {
                GameObject cameraObject = new GameObject("TraceReplayCamera");
                cameraRig = cameraObject.AddComponent<CameraRigController>();
            }

            if (FindObjectOfType<Light>() == null)
            {
                GameObject lightObject = new GameObject("Directional Light");
                Light light = lightObject.AddComponent<Light>();
                light.type = LightType.Directional;
                light.intensity = 1.2f;
                lightObject.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            }

            hudController = FindObjectOfType<ReplayHudController>();
            if (hudController == null)
            {
                GameObject hudObject = new GameObject("ReplayHud");
                hudController = hudObject.AddComponent<ReplayHudController>();
            }

            hudController.Initialize(this);
        }
    }
}
