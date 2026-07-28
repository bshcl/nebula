using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using UnityEngine;

namespace Nebula.Modules.Chat
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

        [Header("API")]
        [SerializeField] private string apiBaseUrl = "http://127.0.0.1:8000/api/v1/completions";

        public event Action<string, int> OnMessageParsed;
        public event Action<string> OnSystemStatusChanged;
        /// <summary>Raised when the stream contains [[GIFT:item]] — gameplay grant hook.</summary>
        public event Action<string> OnGiftReceived;

        private const string SessionPrefsKey = "nebula_unity_session_id";

        private INebulaApiService _apiService;
        private string _currentSessionId = "";

        /// <summary>True after the first Talk message created a session id.</summary>
        public bool HasSession => !string.IsNullOrEmpty(_currentSessionId);

        private Dictionary<string, Action<string>> _actionHandlers;

        private int _tempMoodBuffer = 50;

        private string _streamBuffer = string.Empty;

        /// <summary>http://host/api/v1 — derived from the completions URL.</summary>
        private string ApiV1Root =>
            apiBaseUrl.Replace("/completions", "").TrimEnd('/');

        private const string DefaultQuestId = "quest_first_hello";

        private void Awake()
        {
            _apiService = new NebulaApiService();

            // Session is created only when the player clicks Talk — do not restore on Play.
            _currentSessionId = "";

            _actionHandlers = new Dictionary<string, Action<string>>
            {
                { "MOOD", HandleMoodAction },
                { "GIFT", HandleGiftAction },
                { "ANIM", HandleAnimationAction },
                { "SYSTEM", HandleSystemAction }
            };
        }

        /// <summary>
        /// Creates a session id on first Talk. No-op if one already exists this play.
        /// </summary>
        public void EnsureSession()
        {
            if (!string.IsNullOrEmpty(_currentSessionId))
                return;

            _currentSessionId = "unity-session-" + DateTime.Now.Ticks;
            PlayerPrefs.SetString(SessionPrefsKey, _currentSessionId);
            PlayerPrefs.Save();
            Debug.Log($"[Manager] New session started: {_currentSessionId}");
        }

        public async Task<List<string>> FetchInventoryLinesAsync()
        {
            if (string.IsNullOrEmpty(_currentSessionId))
                return new List<string>();

            var resp = await _apiService.GetInventoryAsync(ApiV1Root, _currentSessionId);
            var list = new List<string>();
            if (resp?.Data?.Items == null) return list;
            foreach (var item in resp.Data.Items)
                list.Add($"{item.ItemId} x{item.Qty}");
            return list;
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
            if (string.IsNullOrWhiteSpace(itemName))
            {
                Debug.LogWarning("[Manager] Gift signal ignored: empty item name");
                return;
            }

            string cleaned = itemName.Trim();
            Debug.Log($"[Manager] Gift granted: {cleaned}");
            OnGiftReceived?.Invoke(cleaned);

            // Light feedback: celebrate with Wave when the animator supports it.
            HandleAnimationAction("WAVE");
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

        /// <summary>
        /// Entry point called by the chat UI.
        /// </summary>
        public async Task SendUserMessage(string userText)
        {
            try
            {
                if (string.IsNullOrEmpty(_currentSessionId))
                    EnsureSession();

                var requestData = new ChatRequest
                {
                    SessionId = _currentSessionId,
                    Message = userText,
                    BotName = botName,
                    BotPersonality = botPersonality,
                    History = new List<ChatMessage>()
                };

                await _apiService.PostChatAsync(apiBaseUrl, requestData, ProcessIncomingChunk);

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
        /// Turn in default quest: check status first, then ready (if needed) + claim.
        /// Already-claimed quests return a soft message instead of spamming HTTP 400.
        /// </summary>
        public async Task<string> ClaimDefaultQuestAsync()
        {
            try
            {
                if (string.IsNullOrEmpty(_currentSessionId))
                    return "Talk to the NPC first (no session yet)";

                var statusResp = await _apiService.GetQuestStatusAsync(
                    ApiV1Root, _currentSessionId, DefaultQuestId);
                string questStatus = statusResp?.Data?.QuestStatus;

                if (questStatus == "claimed")
                    return "Quest already claimed";

                if (questStatus != "ready_to_claim")
                {
                    var readyResp = await _apiService.MarkQuestReadyAsync(
                        ApiV1Root, _currentSessionId, DefaultQuestId);
                    questStatus = readyResp?.Data?.QuestStatus;
                    if (questStatus != "ready_to_claim")
                        return "Quest not ready yet";
                }

                var claimResp = await _apiService.ClaimQuestAsync(
                    ApiV1Root, _currentSessionId, DefaultQuestId);
                if (claimResp?.Data?.Grant == null)
                    return "Claim succeeded but grant payload was empty";

                OnGiftReceived?.Invoke(claimResp.Data.Grant.ItemId);
                return $"Claimed {claimResp.Data.Grant.ItemId} x{claimResp.Data.Grant.GrantedQty}";
            }
            catch (Exception e)
            {
                // Soften duplicate-claim races that slip past the status check.
                if (e.Message.IndexOf("already claimed", StringComparison.OrdinalIgnoreCase) >= 0)
                    return "Quest already claimed";

                Debug.LogError($"[Manager] Claim default quest failed: {e.Message}");
                return $"Claim failed: {e.Message}";
            }
        }
    }
}