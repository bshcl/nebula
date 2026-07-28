using System;
using System.Threading.Tasks;

namespace Nebula.Modules.Chat
{
    public interface INebulaApiService
    {
        /// <summary>
        /// Posts a chat request and invokes onChunkReceived for each streamed text chunk.
        /// </summary>
        Task PostChatAsync(string apiUrl, ChatRequest request, Action<string> onChunkReceived);

        /// <summary>
        /// Gets the inventory for a session and returns an InventoryResponse.
        /// </summary>
        Task<InventoryResponse> GetInventoryAsync(string apiUrl, string sessionId);

        Task<QuestStatusResponse> GetQuestStatusAsync(string apiUrl, string sessionId, string questId);

        Task<QuestStatusResponse> MarkQuestReadyAsync(string apiUrl, string sessionId, string questId);

        Task<QuestClaimResponse> ClaimQuestAsync(string apiUrl, string sessionId, string questId);
    }
}
