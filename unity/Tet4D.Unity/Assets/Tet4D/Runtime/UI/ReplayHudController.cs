using System.Collections.Generic;
using Tet4D.UnityReplay.TraceReplay;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tet4D.UnityReplay.UI
{
    public sealed class ReplayHudController : MonoBehaviour
    {
        private TraceReplayController controller;
        private UIDocument document;
        private DropdownField traceTypeDropdown;
        private DropdownField caseDropdown;
        private Button prevButton;
        private Button playButton;
        private Button nextButton;
        private Button resetButton;
        private Slider speedSlider;
        private Toggle diagnosticsToggle;
        private Label statusLabel;
        private Label frameLabel;
        private Label metadataLabel;
        private Label diagnosticsLabel;
        private ScrollView diagnosticsScroll;
        private bool suppressCallbacks;

        public void Initialize(TraceReplayController replayController)
        {
            controller = replayController;
            EnsureDocument();
            BindControls();
        }

        private void Update()
        {
            if (controller == null || statusLabel == null)
            {
                return;
            }

            Refresh();
        }

        private void EnsureDocument()
        {
            document = GetComponent<UIDocument>();
            if (document == null)
            {
                document = gameObject.AddComponent<UIDocument>();
            }

            if (document.panelSettings == null)
            {
                document.panelSettings = ScriptableObject.CreateInstance<PanelSettings>();
            }

            VisualTreeAsset layout = Resources.Load<VisualTreeAsset>("Tet4D/ReplayHud");
            StyleSheet styles = Resources.Load<StyleSheet>("Tet4D/ReplayHud");
            document.rootVisualElement.Clear();
            if (layout != null)
            {
                layout.CloneTree(document.rootVisualElement);
            }
            else
            {
                document.rootVisualElement.Add(new Label("Replay HUD asset missing."));
            }

            if (styles != null)
            {
                document.rootVisualElement.styleSheets.Add(styles);
            }
        }

        private void BindControls()
        {
            VisualElement root = document.rootVisualElement;
            statusLabel = root.Q<Label>("status-label");
            frameLabel = root.Q<Label>("frame-label");
            metadataLabel = root.Q<Label>("metadata-label");
            diagnosticsLabel = root.Q<Label>("diagnostics-text");
            diagnosticsScroll = root.Q<ScrollView>("diagnostics-scroll");
            traceTypeDropdown = root.Q<DropdownField>("trace-type-dropdown");
            caseDropdown = root.Q<DropdownField>("case-dropdown");
            prevButton = root.Q<Button>("prev-button");
            playButton = root.Q<Button>("play-button");
            nextButton = root.Q<Button>("next-button");
            resetButton = root.Q<Button>("reset-button");
            speedSlider = root.Q<Slider>("speed-slider");
            diagnosticsToggle = root.Q<Toggle>("diagnostics-toggle");

            if (prevButton != null)
            {
                prevButton.clicked += delegate { controller.StepFrame(-1); };
            }

            if (playButton != null)
            {
                playButton.clicked += delegate { controller.TogglePlayback(); };
            }

            if (nextButton != null)
            {
                nextButton.clicked += delegate { controller.StepFrame(1); };
            }

            if (resetButton != null)
            {
                resetButton.clicked += delegate { controller.ResetPlayback(); };
            }

            if (speedSlider != null)
            {
                speedSlider.RegisterValueChangedCallback(
                    delegate(ChangeEvent<float> evt)
                    {
                        if (!suppressCallbacks)
                        {
                            controller.SetPlaybackSpeed(evt.newValue);
                        }
                    }
                );
            }

            if (diagnosticsToggle != null)
            {
                diagnosticsToggle.RegisterValueChangedCallback(
                    delegate(ChangeEvent<bool> evt)
                    {
                        if (!suppressCallbacks)
                        {
                            controller.SetDiagnosticsVisible(evt.newValue);
                        }
                    }
                );
            }

            if (traceTypeDropdown != null)
            {
                traceTypeDropdown.RegisterValueChangedCallback(
                    delegate(ChangeEvent<string> evt)
                    {
                        if (!suppressCallbacks)
                        {
                            controller.SelectTraceType(evt.newValue);
                        }
                    }
                );
            }

            if (caseDropdown != null)
            {
                caseDropdown.RegisterValueChangedCallback(
                    delegate(ChangeEvent<string> evt)
                    {
                        if (!suppressCallbacks)
                        {
                            controller.SelectCase(evt.newValue);
                        }
                    }
                );
            }
        }

        private void Refresh()
        {
            suppressCallbacks = true;
            if (statusLabel != null)
            {
                statusLabel.text = controller.StatusMessage;
            }

            if (traceTypeDropdown != null)
            {
                traceTypeDropdown.choices = new List<string>(controller.TraceTypes);
                traceTypeDropdown.value = controller.CurrentTraceType;
            }

            if (caseDropdown != null)
            {
                caseDropdown.choices = new List<string>(controller.CurrentCaseIds);
                caseDropdown.value = controller.CurrentCaseId;
            }

            if (frameLabel != null)
            {
                frameLabel.text = controller.FrameSummary;
            }

            if (metadataLabel != null)
            {
                metadataLabel.text = controller.MetadataText;
            }

            if (diagnosticsLabel != null)
            {
                diagnosticsLabel.text = controller.DiagnosticsText;
            }

            if (playButton != null)
            {
                playButton.text = controller.IsPlaying ? "Pause" : "Play";
            }

            if (speedSlider != null)
            {
                speedSlider.value = controller.PlaybackSpeed;
            }

            if (diagnosticsToggle != null)
            {
                diagnosticsToggle.value = controller.DiagnosticsVisible;
            }

            if (diagnosticsScroll != null)
            {
                diagnosticsScroll.style.display = controller.DiagnosticsVisible
                    ? DisplayStyle.Flex
                    : DisplayStyle.None;
            }

            suppressCallbacks = false;
        }
    }
}
