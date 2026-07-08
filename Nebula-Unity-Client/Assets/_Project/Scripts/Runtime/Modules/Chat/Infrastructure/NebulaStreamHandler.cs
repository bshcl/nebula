using System;
using System.Text;
using UnityEngine.Networking;

namespace Nebula.Modules.Chat
{
    /// <summary>
    /// Streams raw UTF-8 chunks from UnityWebRequest to subscribers.
    /// </summary>
    public class NebulaStreamHandler : DownloadHandlerScript
    {
        public event Action<string> OnChunkReceived;

        // Parent class requires a buffer; we forward chunks immediately instead of accumulating.
        public NebulaStreamHandler() : base(new byte[1024 * 64]) { }

        protected override bool ReceiveData(byte[] data, int dataLength)
        {
            if (data == null || dataLength == 0) return false;

            string chunk = Encoding.UTF8.GetString(data, 0, dataLength);
            OnChunkReceived?.Invoke(chunk);

            return true;
        }
    }
}
