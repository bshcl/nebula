using System;
using System.Text;
using System.Threading.Tasks;
using Nebula.Core;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.Networking;

namespace Nebula.Net
{
    public class NebulaApiService : INebulaApiService
    {
        private const string DefaultApiUrl = "http://127.0.0.1:8000/api/v1/completions";

        public async Task PostChatAsync(string apiUrl, ChatRequest request, Action<string> onChunkReceived)
        {
            string url = string.IsNullOrWhiteSpace(apiUrl) ? DefaultApiUrl : apiUrl;
            string json = JsonConvert.SerializeObject(request);
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

            using var req = new UnityWebRequest(url, NebulaConstants.RestfulConstants.POST);
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

        public async Task<InventoryResponse> GetInventoryAsync(string apiUrl, string sessionId)
        {
            // apiUrl example: http://localhost:8000/api/v1
            string url = $"{apiUrl.TrimEnd('/')}/inventory/{sessionId}";
            using var req = UnityWebRequest.Get(url);
            var op = req.SendWebRequest();
            while (!op.isDone) await Task.Yield();

            if (req.result != UnityWebRequest.Result.Success)
            {
                throw new Exception($"Inventory request failed: {req.error}");
            }
            return JsonConvert.DeserializeObject<InventoryResponse>(req.downloadHandler.text);
        }



        public async Task<QuestStatusResponse> GetQuestStatusAsync(string apiUrl, string sessionId, string questId)
        {
            string url = $"{apiUrl.TrimEnd('/')}/quests/{sessionId}/{questId}";
            using var req = UnityWebRequest.Get(url);
            var op = req.SendWebRequest();
            while (!op.isDone) await Task.Yield();

            if (req.result != UnityWebRequest.Result.Success)
                throw new Exception($"Get quest status failed: {req.responseCode} {req.downloadHandler.text}");
            return JsonConvert.DeserializeObject<QuestStatusResponse>(req.downloadHandler.text);
        }

        public async Task<QuestClaimResponse> ClaimQuestAsync(string apiUrl, string sessionId, string questId)
        {
            string url = $"{apiUrl.TrimEnd('/')}/quests/{sessionId}/{questId}/claim";
            using var req = new UnityWebRequest(url, NebulaConstants.RestfulConstants.POST);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader(
                NebulaConstants.RestfulConstants.CONTENT_TYPE,
                NebulaConstants.RestfulConstants.APPLICATION_JSON);

            req.uploadHandler = new UploadHandlerRaw(Array.Empty<byte>());
            var op = req.SendWebRequest();
            while (!op.isDone) await Task.Yield();

            if (req.result != UnityWebRequest.Result.Success)
                throw new Exception($"Claim failed: {req.responseCode} {req.downloadHandler.text}");
            return JsonConvert.DeserializeObject<QuestClaimResponse>(req.downloadHandler.text);
        }

        public async Task<QuestStatusResponse> MarkQuestReadyAsync(string apiUrl, string sessionId, string questId)
        {
            string url = $"{apiUrl.TrimEnd('/')}/quests/{sessionId}/{questId}/ready";
            using var req = new UnityWebRequest(url, NebulaConstants.RestfulConstants.POST);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader(
                NebulaConstants.RestfulConstants.CONTENT_TYPE,
                NebulaConstants.RestfulConstants.APPLICATION_JSON);
            req.uploadHandler = new UploadHandlerRaw(Array.Empty<byte>());
            var op = req.SendWebRequest();
            while (!op.isDone) await Task.Yield();

            if (req.result != UnityWebRequest.Result.Success)
                throw new Exception($"Mark quest ready failed: {req.responseCode} {req.downloadHandler.text}");
            return JsonConvert.DeserializeObject<QuestStatusResponse>(req.downloadHandler.text);
        }
    }
}
