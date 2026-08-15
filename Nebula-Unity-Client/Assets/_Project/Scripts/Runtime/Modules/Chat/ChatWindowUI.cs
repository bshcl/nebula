using System;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Nebula.Modules.Chat
{
    /// <summary>
    /// Chat presentation layer: user input and dialogue rendering only.
    /// Subscribes to NebulaManager events and does not call the API directly.
    /// </summary>
    public class ChatWindowUI : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private TMP_InputField inputField;
        [SerializeField] private Button sendButton;
        [SerializeField] private TextMeshProUGUI dialogueText;
        [SerializeField] private TextMeshProUGUI speakerNameText;
        [SerializeField] private string defaultSpeakerName = "Sakura";
        [Tooltip("Object to show/hide (ChatPanel). If empty, uses this GameObject.")]
        [SerializeField] private GameObject panelRoot;
        [Tooltip("NPC World Space Canvas that holds DialogueText. Shown only when dialogueText is under it.")]
        [SerializeField] private GameObject worldSpaceRoot;

        [Header("Manager")]
        [SerializeField] private NebulaManager nebulaManager;

        private bool _isProcessing;
        private bool _awaitingFirstChunk;
        private bool _subscribed;

        private GameObject Panel => panelRoot != null ? panelRoot : gameObject;

        private void Awake()
        {
            if (worldSpaceRoot != null)
                worldSpaceRoot.SetActive(false);

            // If this script sits on Screen Space Canvas, prefer ChatPanel as panel root.
            if (panelRoot == null && gameObject.name.Contains("Canvas"))
            {
                var chatPanel = transform.Find("ChatPanel");
                if (chatPanel != null)
                    panelRoot = chatPanel.gameObject;
            }

            EnsureUiRefs();
            // Subscribe once; do not unsubscribe when Hide() disables this GameObject,
            // otherwise mid-stream text is dropped while ANIM/MOOD still fire on Manager.
            Subscribe();
        }

        /// <summary>
        /// Prefer Inspector assignment. Auto-bind finds DialogueText / SpeakerName under this object.
        /// </summary>
        private void EnsureUiRefs()
        {
            if (dialogueText == null)
                dialogueText = FindChildTmp("DialogueText");

            if (speakerNameText == null)
                speakerNameText = FindChildTmp("SpeakerName");
        }

        private TextMeshProUGUI FindChildTmp(string objectName)
        {
            foreach (var tmp in GetComponentsInChildren<TextMeshProUGUI>(true))
            {
                if (tmp.gameObject.name != objectName) continue;
                Debug.Log($"[UI] Auto-bound {objectName} on {gameObject.name}");
                return tmp;
            }

            return null;
        }

        public void SetSpeakerName(string name)
        {
            EnsureUiRefs();
            if (speakerNameText == null)
                return;

            string resolved = string.IsNullOrWhiteSpace(name) ? defaultSpeakerName : name;
            if (string.IsNullOrWhiteSpace(resolved))
                resolved = "Sakura";

            speakerNameText.SetText(resolved);
        }

        private void OnDestroy() => Unsubscribe();

        private void Subscribe()
        {
            if (_subscribed || nebulaManager == null) return;
            nebulaManager.OnMessageParsed += UpdateDialogueDisplay;
            nebulaManager.OnGiftReceived += ShowGiftReceived;
            _subscribed = true;
        }

        private void Unsubscribe()
        {
            if (!_subscribed || nebulaManager == null) return;
            nebulaManager.OnMessageParsed -= UpdateDialogueDisplay;
            nebulaManager.OnGiftReceived -= ShowGiftReceived;
            _subscribed = false;
        }

        private void UpdateDialogueDisplay(string cleanText, int mood)
        {
            if (string.IsNullOrEmpty(cleanText)) return;

            EnsureUiRefs();
            if (dialogueText == null) return;

            if (_awaitingFirstChunk)
            {
                SetSpeakerName(defaultSpeakerName);
                if (speakerNameText != null)
                    speakerNameText.gameObject.SetActive(true);
                dialogueText.text = "";
                _awaitingFirstChunk = false;
            }

            dialogueText.text += cleanText;
        }

        private void ShowGiftReceived(string itemName)
        {
            EnsureUiRefs();
            if (dialogueText == null) return;

            SetSpeakerName(defaultSpeakerName);
            if (speakerNameText != null)
                speakerNameText.gameObject.SetActive(true);

            if (_awaitingFirstChunk)
            {
                dialogueText.text = "";
                _awaitingFirstChunk = false;
            }

            dialogueText.text += $"\n<color=#E8B823>[Gift received: {itemName}]</color>\n";
            Debug.Log($"[UI] Gift banner shown: {itemName}");
        }

        /// <summary>
        /// Wire this to the Send button OnClick event.
        /// </summary>
        public async void OnSendClick()
        {
            if (_isProcessing) return;
            if (nebulaManager == null)
            {
                Debug.LogError("[UI] NebulaManager not assigned on ChatWindowUI");
                return;
            }

            if (inputField == null) return;
            string userInput = inputField.text;
            if (string.IsNullOrEmpty(userInput)) return;

            Subscribe();
            EnsureUiRefs();
            SetLoadingState(true);
            _awaitingFirstChunk = true;

            try
            {
                await nebulaManager.SendUserMessage(userInput);
            }
            catch (Exception e)
            {
                Debug.LogError($"[UI] Send failed: {e.Message}");
                if (dialogueText != null)
                    dialogueText.text = "<color=red>Network error. Check that the API is running.</color>";
            }
            finally
            {
                SetLoadingState(false);
                _awaitingFirstChunk = false;
                if (inputField != null)
                    inputField.text = "";
            }
        }

        private void SetLoadingState(bool isLoading)
        {
            _isProcessing = isLoading;
            if (sendButton != null)
                sendButton.interactable = !isLoading;
            if (inputField != null)
                inputField.interactable = !isLoading;

            if (isLoading && dialogueText != null)
                dialogueText.text = "NPC is thinking...";
        }

        public void Show()
        {
            Panel.SetActive(true);
            EnsureUiRefs();

            // Nameplate stays hidden until the first spoken chunk arrives.
            if (speakerNameText != null)
            {
                speakerNameText.text = string.Empty;
                speakerNameText.gameObject.SetActive(false);
            }

            if (worldSpaceRoot != null)
            {
                bool dialogueOnWorld =
                    dialogueText != null &&
                    dialogueText.transform.IsChildOf(worldSpaceRoot.transform);
                worldSpaceRoot.SetActive(dialogueOnWorld);
            }

            Subscribe();
        }

        public void Hide()
        {
            if (dialogueText != null)
                dialogueText.text = string.Empty;

            if (speakerNameText != null)
            {
                speakerNameText.text = string.Empty;
                speakerNameText.gameObject.SetActive(false);
            }

            if (worldSpaceRoot != null)
                worldSpaceRoot.SetActive(false);

            Panel.SetActive(false);
        }
    }
}
