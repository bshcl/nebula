using System;
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
