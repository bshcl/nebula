using Newtonsoft.Json;
using System;
using System.Collections.Generic;


namespace Nebula.Net
{
    [Serializable]
    public class ChatRequest
    {
        [JsonProperty("session_id")]
        public string SessionId;

        [JsonProperty("message")]
        public string Message;

        [JsonProperty("history")]
        public List<ChatMessage> History;

        [JsonProperty("bot_name")]
        public string BotName;

        [JsonProperty("bot_personality")]
        public string BotPersonality;
    }
}
