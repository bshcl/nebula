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
    /// 逻辑指挥官：负责协调网络服务、解析 AI 信号并分发动作指令。
    /// 具备“弹性大脑”感知能力，能识别系统降级信号并通知视觉系统。
    /// </summary>
    public class NebulaManager : MonoBehaviour
    {
        [Header("NPC 配置")]
        [SerializeField] private string botName = "Sakura";
        [SerializeField] private string botPersonality = "傲娇且专业的 3D 引导员";

        [Header("动画引用")]
        [SerializeField] private Animator npcAnimator;

        // [Header("广播频道")]
        // 💡 基础广播：文字内容和心情值
        public event Action<string, int> OnMessageParsed;
        // 💡 系统广播：通知全系统 NPC 的状态变化（如 OFFLINE）
        public event Action<string> OnSystemStatusChanged;

        // 基础设施
        private INebulaApiService _apiService;
        private string _currentSessionId = "";

        // 动作分发字典
        private Dictionary<string, Action<string>> _actionHandlers;

        // 临时存储解析过程中的心情值
        private int _tempMoodBuffer = 50;

        // 💡 信号缓冲区
        private string _streamBuffer = string.Empty; 

        private void Awake()
        {
            _apiService = new NebulaApiService();

            // 1. 初始化分发器：注册所有支持的 AI 指令
            // 这种设计模式让你以后增加新功能（如：更换服装）只需在这里加一行
            _actionHandlers = new Dictionary<string, Action<string>>
            {
                { "MOOD", HandleMoodAction },
                { "GIFT", HandleGiftAction },
                { "ANIM", HandleAnimationAction },
                { "SYSTEM", HandleSystemAction } // 👈 处理来自后端弹性大脑的降级信号
            };
        }

        /// <summary>
        /// 外部 UI 调用的主入口
        /// </summary>
        public async Task SendUserMessage(string userText)
        {
            try
            {
                // 2. 持久化会话 ID 逻辑：确保 NPC 拥有连续记忆
                if (string.IsNullOrEmpty(_currentSessionId))
                {
                    _currentSessionId = "unity-session-" + DateTime.Now.Ticks;
                    Debug.Log($"[Manager] 新会话已开启: {_currentSessionId}");
                }

                var requestData = new ChatRequest
                {
                    SessionId = _currentSessionId,
                    Message = userText,
                    BotName = botName,
                    BotPersonality = botPersonality,
                    History = new List<ChatMessage>()
                };

                await _apiService.PostChatAsync(requestData, (chunk) =>
                {
                    ProcessIncomingChunk(chunk);
                });

                // 💡 架构师补丁：当流结束时，如果缓冲区还有剩下的文字（没有信号标签的）
                // 必须强制清空并广播最后一次，否则最后几个字可能出不来
                if (!string.IsNullOrEmpty(_streamBuffer))
                {
                    // 再次检查是否有遗漏的信号（理论上不会有，除非后端发了一半断了）
                    OnMessageParsed?.Invoke(_streamBuffer, _tempMoodBuffer);
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[Manager] 核心流程异常: {e.Message}");
            }
            finally
            {
                // 💡 请求彻底结束后，清理缓冲区
                _streamBuffer = string.Empty; // 彻底重置，准备下一次对话
            }
        }

        /// <summary>
        /// 💡 核心分拣逻辑：处理每一块到达的文字
        /// </summary>
        private void ProcessIncomingChunk(string chunk)
        {
            // 1. 塞进缓冲区
            _streamBuffer += chunk;

            // 2. 尝试解析缓冲区里的所有完整信号 [[KEY:VAL]]
            string signalPattern = @"\[\[(.*?):(.*?)\]\]";
            var matches = Regex.Matches(_streamBuffer, signalPattern);

            foreach (Match m in matches)
            {
                string key = m.Groups[1].Value.ToUpper(); // 拿到 "SYSTEM"
                string val = m.Groups[2].Value;           // 拿到 "OFFLINE"

                // 执行动作（变色、送礼等）
                if (_actionHandlers.TryGetValue(key, out var handler))
                {
                    handler.Invoke(val);
                }

                // 💡 从缓冲区中移除已处理的信号标签
                _streamBuffer = _streamBuffer.Replace(m.Value, "");
            }

            // 3. 💡 提取“安全”的文字发给 UI
            // 规则：如果缓冲区里还有 '['，说明后面可能跟着信号，先不发 '[' 之后的内容
            int bracketIndex = _streamBuffer.IndexOf('[');

            if (bracketIndex == -1)
            {
                // 没有左括号，说明全是纯文字，全发走 
                if (_streamBuffer.Length > 0)
                {
                    OnMessageParsed?.Invoke(_streamBuffer, _tempMoodBuffer);
                    _streamBuffer = "";// 发完清空
                }
            }
            else if (bracketIndex > 0)
            {
                // 有左括号，但左括号前面有文字
                // 把左括号前面的文字发走，剩下的留在缓冲区等 ']]'
                string safeText = _streamBuffer.Substring(0, bracketIndex);
                OnMessageParsed?.Invoke(safeText, _tempMoodBuffer);
                _streamBuffer = _streamBuffer.Substring(bracketIndex);
            }
        }

        // ==========================================
        // 原子化动作处理器 (私有方法)
        // ==========================================

        private void HandleMoodAction(string value)
        {
            if (int.TryParse(value, out int mood))
            {
                _tempMoodBuffer = mood;
                Debug.Log($"[Manager] 心情指令已处理: {mood}");
            }
        }

        private void HandleSystemAction(string status)
        {
            // 💡 架构师提示：当收到 OFFLINE 时，意味着后端已降级到本地模型
            if (status == "OFFLINE")
            {
                Debug.LogWarning("[Manager] ⚠️ 检测到 NPC 进入离线/虚弱模式");
                // 广播给视觉系统，让 NPC 表现出“身体不适”
                OnSystemStatusChanged?.Invoke("OFFLINE");
            }
        }

        private void HandleGiftAction(string itemName)
        {
            Debug.Log($"[Manager] 🎁 触发道具发放逻辑: {itemName}");
        }

        private void HandleAnimationAction(string animName)
        {
            Debug.Log($"[Manager] 💃 触发动画切换指令: {animName}");

            if (npcAnimator == null) return;

            // 💡 架构师提示：将 AI 发来的字符串转换为 Animator 的 Trigger
            // 比如 AI 发来 [[ANIM:WAVE]]，这里 animName 就是 "WAVE"
            // 我们将其转为首字母大写以匹配 Unity 规范
            string triggerName = System.Globalization.CultureInfo.CurrentCulture.TextInfo.ToTitleCase(animName.ToLower());

            try
            {
                // 💡 架构师提示：先检查参数是否存在，防止 Unity 报警告
                if (HasParameter(npcAnimator, triggerName))
                {
                    npcAnimator.SetTrigger(triggerName);
                    Debug.Log($"[Manager] 💃 成功触发动画: {triggerName}");
                }
                else
                {
                    Debug.LogWarning($"[Manager] AI 想要执行动作 {triggerName}，但你还没在 Animator 里定义它。");
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[Manager] 无法触发动画 {triggerName}: {e.Message}");
            }
        }

        // 辅助函数：检查 Animator 是否包含某个参数
        private bool HasParameter(Animator animator, string paramName)
        {
            foreach (AnimatorControllerParameter param in animator.parameters)
            {
                if (param.name == paramName) return true;
            }
            return false;
        }
    }
}