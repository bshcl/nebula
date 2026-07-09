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
    }
}
