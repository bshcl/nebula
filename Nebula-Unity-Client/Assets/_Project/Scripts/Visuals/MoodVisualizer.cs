using Nebula.Controllers;
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