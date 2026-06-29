using System;
using Newtonsoft.Json;

namespace Nebula.Models
{
    [Serializable]
    public class ChatResponse
    {
        [JsonProperty("status")]
        public string Status;

        [JsonProperty("reply")]
        public string Reply;

        [JsonProperty("conversation_id")]
        public string ConversationId;
    }
}