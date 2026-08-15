using System;
using Newtonsoft.Json;

namespace Nebula.Net
{
	public class ChatMessage
	{
        [JsonProperty("role")]
        public string Role;

        [JsonProperty("content")]
        public string Content;
    }
}