using Nebula.Framework;
using Newtonsoft.Json;
using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace Nebula.Modules.Chat
{
    public class NebulaApiService : INebulaApiService
    {
        private const string DefaultApiUrl = "http://localhost:8000/api/v1/completions";

        public async Task PostChatAsync(string apiUrl, ChatRequest request, Action<string> onChunkReceived)
        {
            string url = string.IsNullOrWhiteSpace(apiUrl) ? DefaultApiUrl : apiUrl;
            string json = JsonConvert.SerializeObject(request);
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

            using (UnityWebRequest req = new UnityWebRequest(url, NebulaConstants.RestfulConstants.POST))
            {
                var streamHandler = new NebulaStreamHandler();
                streamHandler.OnChunkReceived += chunk => onChunkReceived?.Invoke(chunk);

                req.uploadHandler = new UploadHandlerRaw(bodyRaw);
                req.downloadHandler = streamHandler;
                req.SetRequestHeader(
                    NebulaConstants.RestfulConstants.CONTENT_TYPE,
                    NebulaConstants.RestfulConstants.APPLICATION_JSON);

                var operation = req.SendWebRequest();

                while (!operation.isDone)
                {
                    await Task.Yield();
                }

                if (req.result != UnityWebRequest.Result.Success)
                {
                    throw new Exception($"Stream request failed: {req.error}");
                }
            }
        }
    }
}
