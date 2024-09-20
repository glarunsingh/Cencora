export const environment = {
    production: false,
    api_url: 'https://app-keyaccount-qa.azurewebsites.net/',
    clientId: '109ec945-2f44-467d-a58c-621d3e58671c', // Application (client) ID from the app registration
    authority: 'https://login.microsoftonline.com/0b5ac31e-e17a-4021-9d04-550f86320765', // The Azure cloud instance and the app's sign-in audience (tenant ID, common, organizations, or consumers)
    tenantId: "0b5ac31e-e17a-4021-9d04-550f86320765",
    // redirectUri: 'http://localhost:4200/',// This is your redirect URI
    redirectUri: 'https://keyaccountdigestqa.azureedge.net',
    navigateToLoginRequestUrl: true,
    custom_scope: "api://45353350-7eb7-43ef-afd2-5d6e390c3983/"
};
