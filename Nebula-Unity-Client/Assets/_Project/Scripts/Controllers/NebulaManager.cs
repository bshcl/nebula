using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using UnityEngine;
using Nebula.Interfaces;
using Nebula.Models;
using Nebula.Services;

namespace Nebula.Controllers
{
    /// <summary>
    /// Coordinates API calls, parses in-band signals, and dispatches NPC actions.
    /// Recognizes backend degradation signals (e.g. SYSTEM:OFFLINE) for the visual layer.
    /// </summary>
    public class NebulaManager : MonoBehaviour
    {
        [Header("NPC Settings")]
        [SerializeField] private string botName = "Sakura";
        [SerializeField] private string botPersonality = "tsundere professional 3D guide";

        [Header("Animation")]
        [SerializeField] private Animator npcAnimator;

        public event Action<string, int> OnMessageParsed;
        public event Action<string> OnSystemStatusChanged;

        private INebulaApiService _apiService;
        private string _currentSessionId = "";

        private Dictionary<string, Action<string>> _actionHandlers;

        private int _tempMoodBuffer = 50;

        private string _streamBuffer = string.Empty;

        private void Awake()
        {
            _apiService = new NebulaApiService();

            _actionHandlers = new Dictionary<string, Action<string>>
            {
                { "MOOD", HandleMoodAction },
                { "GIFT", HandleGiftAction },
                { "ANIM", HandleAnimationAction },
                { "SYSTEM", HandleSystemAction }
            };
        }

        /// <summary>
        /// Entry point called by the chat UI.
        /// </summary>
        public async Task SendUserMessage(string userText)
        {
            try
            {
                if (string.IsNullOrEmpty(_currentSessionId))
                {
                    _currentSessionId = "unity-session-" + DateTime.Now.Ticks;
                    Debug.Log($"[Manager] New session started: {_currentSessionId}");
                }

                var requestData = new ChatRequest
                {
                    SessionId = _currentSessionId,
                    Message = userText,
                    BotName = botName,
                    BotPersonality = botPersonality,
                    History = new List<ChatMessage>()
                };

                await _apiService.PostChatAsync(requestData, ProcessIncomingChunk);

                // Flush any remaining plain text after the stream ends.
                if (!string.IsNullOrEmpty(_streamBuffer))
                {
                    OnMessageParsed?.Invoke(_streamBuffer, _tempMoodBuffer);
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[Manager] Chat flow failed: {e.Message}");
                throw;
            }
            finally
            {
                _streamBuffer = string.Empty;
            }
        }

        /// <summary>
        /// Parses each streamed chunk and dispatches signals such as [[MOOD:n]].
        /// </summary>
        private void ProcessIncomingChunk(string chunk)
        {
            _streamBuffer += chunk;

            const string signalPattern = @"\[\[(.*?):(.*?)\]\]";
            var matches = Regex.Matches(_streamBuffer, signalPattern);

            foreach (Match m in matches)
            {
                string key = m.Groups[1].Value.ToUpper();
                string val = m.Groups[2].Value;

                if (_actionHandlers.TryGetValue(key, out var handler))
                {
                    handler.Invoke(val);
                }

                _streamBuffer = _streamBuffer.Replace(m.Value, "");
            }

            // Emit safe plain text; hold back partial signal prefixes that start with '['.
            int bracketIndex = _streamBuffer.IndexOf('[');

            if (bracketIndex == -1)
            {
                if (_streamBuffer.Length > 0)
                {
                    OnMessageParsed?.Invoke(_streamBuffer, _tempMoodBuffer);
                    _streamBuffer = "";
                }
            }
            else if (bracketIndex > 0)
            {
                string safeText = _streamBuffer.Substring(0, bracketIndex);
                OnMessageParsed?.Invoke(safeText, _tempMoodBuffer);
                _streamBuffer = _streamBuffer.Substring(bracketIndex);
            }
        }

        private void HandleMoodAction(string value)
        {
            if (int.TryParse(value, out int mood))
            {
                _tempMoodBuffer = mood;
                Debug.Log($"[Manager] Mood signal handled: {mood}");
            }
        }

        private void HandleSystemAction(string status)
        {
            if (status == "OFFLINE")
            {
                Debug.LogWarning("[Manager] NPC entered offline/degraded mode");
                OnSystemStatusChanged?.Invoke("OFFLINE");
            }
        }

        private void HandleGiftAction(string itemName)
        {
            Debug.Log($"[Manager] Gift triggered: {itemName}");
        }

        private void HandleAnimationAction(string animName)
        {
            Debug.Log($"[Manager] Animation signal: {animName}");

            if (npcAnimator == null) return;

            string triggerName = System.Globalization.CultureInfo.CurrentCulture.TextInfo.ToTitleCase(animName.ToLower());

            try
            {
                if (HasParameter(npcAnimator, triggerName))
                {
                    npcAnimator.SetTrigger(triggerName);
                    Debug.Log($"[Manager] Animation triggered: {triggerName}");
                }
                else
                {
                    Debug.LogWarning($"[Manager] Animator has no trigger named '{triggerName}'.");
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[Manager] Failed to trigger animation '{triggerName}': {e.Message}");
            }
        }

        private static bool HasParameter(Animator animator, string paramName)
        {
            foreach (AnimatorControllerParameter param in animator.parameters)
            {
                if (param.name == paramName) return true;
            }
            return false;
        }
    }
}
