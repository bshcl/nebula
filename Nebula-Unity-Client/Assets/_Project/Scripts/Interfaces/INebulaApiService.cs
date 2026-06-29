using Nebula.Models;
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
