using Nebula.Models;
using System;
using System.Threading.Tasks;

namespace Nebula.Interfaces
{
    public interface INebulaApiService
    {
        /// <summary>
        /// Posts a chat request and invokes onChunkReceived for each streamed text chunk.
        /// </summary>
        Task PostChatAsync(ChatRequest request, Action<string> onChunkReceived);
    }
}
