using System;
using Newtonsoft.Json;

namespace Nebula.Models
{
	public class ChatMessage
	{
        [JsonProperty("role")]
        public string Role;

        [JsonProperty("content")]
        public string Content;
    }
}