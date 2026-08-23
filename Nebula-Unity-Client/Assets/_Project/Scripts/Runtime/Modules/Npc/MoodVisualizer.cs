using System.Collections;
using Nebula.Modules.Chat;
using UnityEngine;

namespace Nebula.Modules.Npc
{
    /// <summary>
    /// Drives resonance visuals on an aura/core renderer instead of tinting skin.
    /// </summary>
    public class MoodVisualizer : MonoBehaviour
    {
        [Header("Manager")]
        [SerializeField] private NebulaManager nebulaManager;

        [Header("Visual Settings")]
        [SerializeField] private Renderer auraRenderer;
        [SerializeField] private Renderer npcRenderer;
        [SerializeField] private Color happyColor = new Color(0.2f, 1f, 0.65f, 1f);
        [SerializeField] private Color neutralColor = new Color(0.35f, 0.85f, 1f, 1f);
        [SerializeField] private Color angryColor = new Color(1f, 0.25f, 0.35f, 1f);
        [SerializeField] private Color offLineColor = new Color(0.35f, 0.35f, 0.4f, 1f);
        [SerializeField] private float transitionDuration = 1.0f;
        [SerializeField] private float emissionBoost = 2.5f;

        private bool _isOffline;
        private Color _lastMoodColor = Color.white;
        private Coroutine _activeTransition;
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int ColorId = Shader.PropertyToID("_Color");
        private static readonly int EmissionColorId = Shader.PropertyToID("_EmissionColor");

        private Renderer TargetRenderer => auraRenderer != null ? auraRenderer : npcRenderer;

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
            if (TargetRenderer == null) return;

            Color targetColor = CalculateMoodColor(mood);
            _lastMoodColor = targetColor;

            if (_isOffline) return;

            StartColorTransition(targetColor);
        }

        private void StartColorTransition(Color targetColor)
        {
            if (TargetRenderer == null) return;
            if (_activeTransition != null) StopCoroutine(_activeTransition);

            _activeTransition = StartCoroutine(ColorLerpRoutine(targetColor));
        }

        private IEnumerator ColorLerpRoutine(Color targetColor)
        {
            float elapsed = 0f;
            Material mat = TargetRenderer.material;
            Color startColor = ReadColor(mat);

            while (elapsed < transitionDuration)
            {
                elapsed += Time.deltaTime;
                float t = elapsed / transitionDuration;
                ApplyColor(mat, Color.Lerp(startColor, targetColor, t));
                yield return null;
            }

            ApplyColor(mat, targetColor);
            _activeTransition = null;
        }

        private void ApplyColor(Material mat, Color color)
        {
            if (mat.HasProperty(BaseColorId))
                mat.SetColor(BaseColorId, color);
            else if (mat.HasProperty(ColorId))
                mat.SetColor(ColorId, color);
            else
                mat.color = color;

            if (mat.HasProperty(EmissionColorId))
            {
                mat.EnableKeyword("_EMISSION");
                mat.SetColor(EmissionColorId, color * emissionBoost);
            }
        }

        private Color ReadColor(Material mat)
        {
            if (mat.HasProperty(EmissionColorId))
            {
                Color e = mat.GetColor(EmissionColorId);
                if (e.maxColorComponent > 0.01f)
                    return e / Mathf.Max(emissionBoost, 0.01f);
            }

            if (mat.HasProperty(BaseColorId))
                return mat.GetColor(BaseColorId);
            if (mat.HasProperty(ColorId))
                return mat.GetColor(ColorId);
            return mat.color;
        }

        private Color CalculateMoodColor(int mood)
        {
            if (mood <= 40) return angryColor;
            if (mood >= 70) return happyColor;
            return neutralColor;
        }
    }
}
