using System.Collections;
using UnityEngine;

namespace Nebula.Modules.Chat
{
    public class MoodVisualizer : MonoBehaviour
    {
        [Header("Manager")]
        [SerializeField] private NebulaManager nebulaManager;

        [Header("Visual Settings")]
        [SerializeField] private Renderer npcRenderer;
        [SerializeField] private Color happyColor = Color.green;
        [SerializeField] private Color neutralColor = Color.white;
        [SerializeField] private Color angryColor = Color.red;
        [SerializeField] private Color offLineColor = Color.gray;
        [SerializeField] private float transitionDuration = 1.0f;

        private bool _isOffline;
        private Color _lastMoodColor = Color.white;
        private Coroutine _activeTransition;

        private void OnEnable()
        {
            if (nebulaManager != null)
            {
                nebulaManager.OnMessageParsed += UpdateVisuals;
                nebulaManager.OnSystemStatusChanged += HandleSystemStatus;
            }
        }

        private void OnDisable()
        {
            if (nebulaManager != null)
            {
                nebulaManager.OnMessageParsed -= UpdateVisuals;
                nebulaManager.OnSystemStatusChanged -= HandleSystemStatus;
            }
        }

        private void HandleSystemStatus(string status)
        {
            if (status == "OFFLINE")
            {
                _isOffline = true;
                StartColorTransition(offLineColor);
                Debug.Log("[Visuals] System degraded: transitioning to offline appearance");
            }
            else
            {
                _isOffline = false;
                StartColorTransition(_lastMoodColor);
            }
        }

        private void UpdateVisuals(string text, int mood)
        {
            if (npcRenderer == null) return;

            Color targetColor = CalculateMoodColor(mood);
            _lastMoodColor = targetColor;

            if (_isOffline) return;

            StartColorTransition(targetColor);
        }

        private void StartColorTransition(Color targetColor)
        {
            if (_activeTransition != null) StopCoroutine(_activeTransition);

            _activeTransition = StartCoroutine(ColorLerpRoutine(targetColor));
        }

        private IEnumerator ColorLerpRoutine(Color targetColor)
        {
            float elapsed = 0f;
            Color startColor = npcRenderer.material.color;

            while (elapsed < transitionDuration)
            {
                elapsed += Time.deltaTime;
                float t = elapsed / transitionDuration;

                npcRenderer.material.color = Color.Lerp(startColor, targetColor, t);

                yield return null;
            }

            npcRenderer.material.color = targetColor;
            _activeTransition = null;
        }

        private Color CalculateMoodColor(int mood)
        {
            if (mood <= 40) return angryColor;
            if (mood >= 70) return happyColor;
            return neutralColor;
        }
    }
}
