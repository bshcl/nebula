# 🧊 Nebula System | Unity 身体架构文档

## 1. 脚本目录结构
```text
Scripts/
    NEBULA_UNITY_CONTEXT.md
    Controllers/
        NebulaManager.cs
    Core/
        NebulaConstants.cs
        NebulaUtils.cs
    Interfaces/
        INebulaApiService.cs
        impl/
    Models/
        ChatMessage.cs
        ChatRequest.cs
        ChatResponse.cs
    Services/
        NebulaApiService.cs
        NebulaStreamHandler.cs
    UI/
        ChatWindowUI.cs
    Visuals/
        MoodVisualizer.cs
```

## 2. C# 核心源代码

### 文件: Controllers\NebulaManager.cs
```csharp
﻿using System;
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
```

### 文件: Core\NebulaConstants.cs
```csharp
﻿using System;
using System.Collections.Generic;
using System.Text;

namespace Nebula.Core
{
    internal class NebulaConstants
    {
        /// <summary>
        /// RESTful协议相关常量
        /// </summary>
        public static class RestfulConstants
        {
            #region Http Method

            public const string GET = "GET";
            public const string POST = "POST";
            public const string PUT = "PUT";
            public const string DELETE = "DELETE";
            public const string PATCH = "PATCH";

            #endregion

            #region Content-Type

            public const string APPLICATION_JSON = "application/json";

            public const string APPLICATION_XML = "application/xml";

            public const string FORM_URLENCODED =
                "application/x-www-form-urlencoded";

            public const string MULTIPART_FORM_DATA =
                "multipart/form-data";

            #endregion

            #region Header

            public const string AUTHORIZATION = "Authorization";

            public const string CONTENT_TYPE = "Content-Type";

            public const string ACCEPT = "Accept";

            #endregion

            #region Status Code

            public const int OK = 200;

            public const int CREATED = 201;

            public const int NO_CONTENT = 204;

            public const int BAD_REQUEST = 400;

            public const int UNAUTHORIZED = 401;

            public const int FORBIDDEN = 403;

            public const int NOT_FOUND = 404;

            public const int INTERNAL_SERVER_ERROR = 500;

            #endregion
        }
    }
}

```

### 文件: Core\NebulaUtils.cs
```csharp
﻿using System;
using System.Collections.Generic;
using System.Text;

namespace Nebula.Assets._Project.Scripts.Core
{
    internal class NebulaUtils
    {
    }
}

```

### 文件: Interfaces\INebulaApiService.cs
```csharp
﻿using Nebula.Models;
using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;

namespace Nebula.Interfaces
{
    public interface INebulaApiService
    {
        // 定义一个契约：输入请求对象，异步返回服务器给的原始字符串
        // 💡 架构师提示：增加 onChunkReceived 回调，用于实时推送收到的文字块
        Task PostChatAsync(ChatRequest request, Action<string> onChunkReceived);
    }
}

```

### 文件: Models\ChatMessage.cs
```csharp
﻿using System;
using Newtonsoft.Json;

namespace Nebula.Models
{
	public class ChatMessage
	{
        [JsonProperty("role")]
        public string Role;

        [JsonProperty("content")]
        public string Content;
    }
}
```

### 文件: Models\ChatRequest.cs
```csharp
using Newtonsoft.Json;
using System;
using System.Collections.Generic;


namespace Nebula.Models
{
    [Serializable]
    public class ChatRequest
    {
        [JsonProperty("session_id")]
        public string SessionId;

        [JsonProperty("message")]
        public string Message;

        [JsonProperty("history")]
        public List<ChatMessage> History;

        [JsonProperty("bot_name")]
        public string BotName;

        [JsonProperty("bot_personality")]
        public string BotPersonality;
    }
}

```

### 文件: Models\ChatResponse.cs
```csharp
using System;
using Newtonsoft.Json;

namespace Nebula.Models
{
    [Serializable]
    public class ChatResponse
    {
        [JsonProperty("status")]
        public string Status;

        [JsonProperty("reply")]
        public string Reply;

        [JsonProperty("conversation_id")]
        public string ConversationId;
    }
}
```

### 文件: Services\NebulaApiService.cs
```csharp
﻿using Nebula.Core;
using Nebula.Interfaces;
using Nebula.Models;
using Newtonsoft.Json;
using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace Nebula.Services
{
    // 💡 架构师修正：改为 public，确保全系统可见
    public class NebulaApiService : INebulaApiService
    {
        // 💡 架构师建议：URL 应该属于 Service 的内部配置，不暴露给外部
        private const string DEFAULT_API_URL = "http://localhost:8000/api/v1/completions";

        public async Task PostChatAsync(ChatRequest request, Action<string> onChunkReceived)
        {

            // 1. 序列化
            string json = JsonConvert.SerializeObject(request);
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

            // 2. 发起请求 (使用 using 确保资源释放)
            using (UnityWebRequest req = new UnityWebRequest(DEFAULT_API_URL, NebulaConstants.RestfulConstants.POST))
            {
                // 1. 💡 核心改变：使用自定义的流式处理器
                var streamHandler = new NebulaStreamHandler();

                // 2. 💡 建立对讲机连接：当 Handler 收到数据，立刻触发外部传进来的回调
                streamHandler.OnChunkReceived += (chunk) =>
                {
                    onChunkReceived?.Invoke(chunk);
                };

                req.uploadHandler = new UploadHandlerRaw(bodyRaw);
                req.downloadHandler = streamHandler;// 👈 替换掉原来的 Buffer
                req.SetRequestHeader(NebulaConstants.RestfulConstants.CONTENT_TYPE, NebulaConstants.RestfulConstants.APPLICATION_JSON);

                // 3. 异步等待
                var operation = req.SendWebRequest();

                // 3. 异步等待请求结束
                while (!operation.isDone)
                {
                    await Task.Yield();
                }

                if (req.result != UnityWebRequest.Result.Success)
                {
                    Debug.LogError($"[Service] 流式请求失败: {req.error}");
                }
            }
        }
    }
}
```

### 文件: Services\NebulaStreamHandler.cs
```csharp
﻿using System;
using System.Text;
using UnityEngine.Networking;

namespace Nebula.Services
{
    public class NebulaStreamHandler : DownloadHandlerScript
    {
        // 💡 广播：每收到一小块文字，就发给 Manager
        public event Action<string> OnChunkReceived;

        // 必须提供一个缓冲区，虽然我们不怎么用它，但父类需要
        public NebulaStreamHandler() : base(new byte[1024 * 64]) { }

        protected override bool ReceiveData(byte[] data, int dataLength)
        {
            if (data == null || dataLength == 0) return false;

            // 1. 将字节块转为字符串
            string chunk = Encoding.UTF8.GetString(data, 0, dataLength);

            // 2. 💡 立即通过事件发走，不留存！
            OnChunkReceived?.Invoke(chunk);

            return true;
        }
    }
}

```

### 文件: UI\ChatWindowUI.cs
```csharp
﻿using System;
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
```

### 文件: Visuals\MoodVisualizer.cs
```csharp
﻿using Nebula.Controllers;
using System.Collections;
using UnityEngine;

namespace Nebula.Visuals
{
    public class MoodVisualizer : MonoBehaviour
    {
        [Header("逻辑引用")]
        [SerializeField] private NebulaManager nebulaManager;

        [Header("视觉设置")]
        [SerializeField] private Renderer npcRenderer;
        [SerializeField] private Color happyColor = Color.green;
        [SerializeField] private Color neutralColor = Color.white;
        [SerializeField] private Color angryColor = Color.red;
        [SerializeField] private Color offLineColor = Color.gray;
        [SerializeField] private float transitionDuration = 1.0f; // 渐变时长

        private bool _isOffline = false;
        private Color _lastMoodColor = Color.white;
        private Coroutine _activeTransition; // 记录当前正在运行的渐变任务

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
                // 💡 修正：通过统一入口启动协程
                StartColorTransition(offLineColor);
                Debug.Log("[Visuals] 系统降级：平滑切换至虚弱态");
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

            // 💡 核心逻辑：启动平滑变色
            StartColorTransition(targetColor);
        }

        // 💡 架构师技巧：统一的协程管理方法
        private void StartColorTransition(Color targetColor)
        {
            // 1. 停止正在进行的渐变，防止颜色“打架”
            if (_activeTransition != null) StopCoroutine(_activeTransition);

            // 2. 开启新渐变
            _activeTransition = StartCoroutine(ColorLerpRoutine(targetColor));
        }

        // 💡 核心协程：真正的平滑过渡逻辑
        private IEnumerator ColorLerpRoutine(Color targetColor)
        {
            float elapsed = 0f;
            Color startColor = npcRenderer.material.color;

            // 只要时间没到，就一直循环
            while (elapsed < transitionDuration)
            {
                elapsed += Time.deltaTime; // 累加帧间隔时间
                float t = elapsed / transitionDuration; // 计算进度 (0 to 1)

                // 💡 线性插值应用
                npcRenderer.material.color = Color.Lerp(startColor, targetColor, t);

                // 💡 关键：告诉 Unity 这一帧干完了，下一帧再回来继续 while 循环
                yield return null;
            }

            // 确保最终颜色精准对齐
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
```
