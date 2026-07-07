using System;
using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.UI;
using Nebula.Controllers;

namespace Nebula.UI
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
        private Coroutine _typewriterCoroutine;

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

            if (_typewriterCoroutine != null) StopCoroutine(_typewriterCoroutine);

            _typewriterCoroutine = StartCoroutine(TypewriterRoutine(cleanText));

            Debug.Log("[UI] Dialogue updated from manager broadcast.");
        }

        private IEnumerator TypewriterRoutine(string fullText)
        {
            dialogueText.text = "";

            foreach (char c in fullText)
            {
                dialogueText.text += c;
                yield return new WaitForSeconds(0.03f);
            }

            _typewriterCoroutine = null;
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
