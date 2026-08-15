namespace Nebula.Core
{
    internal static class NebulaConstants
    {
        /// <summary>
        /// HTTP and REST-related constants.
        /// </summary>
        public static class RestfulConstants
        {
            #region Http Method

            public const string GET = "GET";
            public const string POST = "POST";
            public const string PUT = "PUT";
            public const string DELETE = "DELETE";
            public const string PATCH = "PATCH";

            #endregion

            #region Content-Type

            public const string APPLICATION_JSON = "application/json";

            public const string APPLICATION_XML = "application/xml";

            public const string FORM_URLENCODED =
                "application/x-www-form-urlencoded";

            public const string MULTIPART_FORM_DATA =
                "multipart/form-data";

            #endregion

            #region Header

            public const string AUTHORIZATION = "Authorization";

            public const string CONTENT_TYPE = "Content-Type";

            public const string ACCEPT = "Accept";

            #endregion

            #region Status Code

            public const int OK = 200;

            public const int CREATED = 201;

            public const int NO_CONTENT = 204;

            public const int BAD_REQUEST = 400;

            public const int UNAUTHORIZED = 401;

            public const int FORBIDDEN = 403;

            public const int NOT_FOUND = 404;

            public const int INTERNAL_SERVER_ERROR = 500;

            #endregion
        }
    }
}
