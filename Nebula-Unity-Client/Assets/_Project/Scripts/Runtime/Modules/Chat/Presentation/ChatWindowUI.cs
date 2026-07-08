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

        [Header("Manager")]
        [SerializeField] private NebulaManager nebulaManager;

        private bool _isProcessing;
        private bool _awaitingFirstChunk;
        private void OnEnable()
        {
            if (nebulaManager != null)
            {
                nebulaManager.OnMessageParsed += UpdateDialogueDisplay;
            }
        }

        private void OnDisable()
        {
            if (nebulaManager != null)
            {
                nebulaManager.OnMessageParsed -= UpdateDialogueDisplay;
            }
        }

        private void UpdateDialogueDisplay(string cleanText, int mood)
        {
            if (string.IsNullOrEmpty(cleanText)) return;

            if (_awaitingFirstChunk)
            {
                dialogueText.text = "";
                _awaitingFirstChunk = false;
            }

            dialogueText.text += cleanText;
        }

        /// <summary>
        /// Wire this to the Send button OnClick event.
        /// </summary>
        public async void OnSendClick()
        {
            if (_isProcessing) return;

            string userInput = inputField.text;
            if (string.IsNullOrEmpty(userInput)) return;

            SetLoadingState(true);
            _awaitingFirstChunk = true;

            try
            {
                await nebulaManager.SendUserMessage(userInput);
            }
            catch (Exception e)
            {
                Debug.LogError($"[UI] Send failed: {e.Message}");
                dialogueText.text = "<color=red>Network error. Check that the API is running.</color>";
            }
            finally
            {
                SetLoadingState(false);
                _awaitingFirstChunk = false;
                inputField.text = "";
            }
        }

        private void SetLoadingState(bool isLoading)
        {
            _isProcessing = isLoading;
            sendButton.interactable = !isLoading;
            inputField.interactable = !isLoading;

            if (isLoading)
            {
                dialogueText.text = "NPC is thinking...";
            }
        }
    }
}
