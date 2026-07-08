using System;
using Newtonsoft.Json;

namespace Nebula.Modules.Chat
{
	public class ChatMessage
	{
        [JsonProperty("role")]
        public string Role;

        [JsonProperty("content")]
        public string Content;
    }
}