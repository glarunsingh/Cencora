export const environment = {
    production: true,
    // api_url: 'https://app-keyaccountsite-prod.azurewebsites.net/',
    api_url: 'https://keyaccount-gefhb0c5ewdzehh3.a01.azurefd.net/api/',
    clientId: '66ceb736-ad8e-44c1-b745-b5cda42dad14', // Application (client) ID from the app registration
    authority: 'https://login.microsoftonline.com/0b5ac31e-e17a-4021-9d04-550f86320765', // The Azure cloud instance and the app's sign-in audience (tenant ID, common, organizations, or consumers)
    //redirectUri: 'http://localhost:4200/',// This is your redirect URI
    redirectUri: 'https://salesdigest.cencora.com/',
    tenantId: "0b5ac31e-e17a-4021-9d04-550f86320765",
    navigateToLoginRequestUrl: false,
    custom_scope: "api://8fc646b7-8dc5-429d-9f5d-9e38d8102a6a/"
};
