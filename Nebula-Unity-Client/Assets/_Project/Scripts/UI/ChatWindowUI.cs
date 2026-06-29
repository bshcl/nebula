using System;
using TMPro;
using UnityEngine;
using UnityEngine.UI;
using Nebula.Controllers;
using System.Collections; // 确保引用了 Controller 命名空间

namespace Nebula.UI
{
    /// <summary>
    /// 表现层：只负责 UI 交互和文字渲染
    /// 它不关心数据是怎么来的，只负责把听到的广播显示出来
    /// </summary>
    public class ChatWindowUI : MonoBehaviour
    {
        [Header("UI 组件引用")]
        [SerializeField] private TMP_InputField inputField;
        [SerializeField] private Button sendButton;
        [SerializeField] private TextMeshProUGUI dialogueText;

        [Header("逻辑中枢引用")]
        [SerializeField] private NebulaManager nebulaManager;

        private bool _isProcessing = false;
        private Coroutine _typewriterCoroutine;

        // ==========================================
        // 第一部分：订阅广播 (收音机模式)
        // ==========================================

        private void OnEnable()
        {
            // 💡 架构师提示：当这个 UI 开启时，把耳机戴上，听 Manager 的广播
            if (nebulaManager != null)
            {
                nebulaManager.OnMessageParsed += UpdateDialogueDisplay;
            }
        }

        private void OnDisable()
        {
            // 💡 架构师提示：当 UI 关闭时，摘下耳机，防止内存泄漏（Java 里的监听器注销）
            if (nebulaManager != null)
            {
                nebulaManager.OnMessageParsed -= UpdateDialogueDisplay;
            }
        }

        /// <summary>
        /// 监听到广播后的具体动作
        /// </summary>
        private void UpdateDialogueDisplay(string cleanText, int mood)
        {
            if (string.IsNullOrEmpty(cleanText)) return;

            // 1. 如果之前的字还没打完，先掐断它
            if (_typewriterCoroutine != null) StopCoroutine(_typewriterCoroutine);

            // 2. 开启新的打字协程
            _typewriterCoroutine = StartCoroutine(TypewriterRoutine(cleanText));

            Debug.Log($"[UI] 成功接收广播，已更新文字内容。");
        }

        private IEnumerator TypewriterRoutine(string fullText)
        {
            dialogueText.text = "";

            // 💡 逐字显示逻辑
            foreach (char c in fullText)
            {
                dialogueText.text += c;
                // 0.03秒出一个字，这是最接近人类语速的节奏
                yield return new WaitForSeconds(0.03f);
            }

            _typewriterCoroutine = null;
        }

        // ==========================================
        // 第二部分：处理用户输入 (发送指令)
        // ==========================================

        /// <summary>
        /// 绑定到按钮的点击事件
        /// </summary>
        public async void OnSendClick()
        {
            if (_isProcessing) return;

            string userInput = inputField.text;
            if (string.IsNullOrEmpty(userInput)) return;

            // 1. 进入“处理中”状态
            SetLoadingState(true);

            try
            {
                // 2. 💡 核心动作：只管把球踢给 Manager，不关心它怎么处理
                // 我们 await 它，只是为了知道什么时候“处理完”好恢复按钮点击
                await nebulaManager.SendUserMessage(userInput);
            }
            catch (Exception e)
            {
                Debug.LogError($"[UI] 发送失败: {e.Message}");
                dialogueText.text = "<color=red>网络连接异常，请检查后端。</color>";
            }
            finally
            {
                // 3. 恢复状态
                SetLoadingState(false);
                inputField.text = ""; // 清空输入框
            }
        }

        /// <summary>
        /// 统一管理 UI 的锁定状态
        /// </summary>
        private void SetLoadingState(bool isLoading)
        {
            _isProcessing = isLoading;
            sendButton.interactable = !isLoading;
            inputField.interactable = !isLoading;

            if (isLoading)
            {
                dialogueText.text = "NPC 正在思考中...";
            }
        }
    }
}