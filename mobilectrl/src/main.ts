import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { AppModule } from './app/app.module';
import { environment } from './environments/environment';

import Amplify from 'aws-amplify';
import config from "./config";


Amplify.configure({
    Auth: {
        mandatorySignIn: true,
        region: config.cognito.REGION,
        userPoolId: config.cognito.USER_POOL_ID,
        identityPoolId: config.cognito.IDENTITY_POOL_ID,
        userPoolWebClientId: config.cognito.APP_CLIENT_ID
    },
    Storage: {
        region: config.s3.REGION,
        bucket: config.s3.BUCKET,
        identityPoolId: config.cognito.IDENTITY_POOL_ID
    },
    API: {
        endpoints: [
            {
                name: "iotShadowAPIGet",
                endpoint: "https://324pofv0gl.execute-api.us-west-2.amazonaws.com/Prod",
                region: config.apiGateway.REGION
            },
            {
                name: "iotShadowAPIPost",
                endpoint: "https://324pofv0gl.execute-api.us-west-2.amazonaws.com/Prod",
                region: config.apiGateway.REGION
            },
            {
                name: "iotTelemetryAPIGet",
                endpoint: "https://fadml3umv8.execute-api.us-west-2.amazonaws.com/Prod",
                region: config.apiGateway.REGION
            },
        ]
    }
});


if (environment.production) {
  enableProdMode();
}

platformBrowserDynamic().bootstrapModule(AppModule)
  .catch(err => console.log(err));
