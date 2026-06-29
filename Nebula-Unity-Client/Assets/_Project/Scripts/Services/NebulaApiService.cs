using Nebula.Core;
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