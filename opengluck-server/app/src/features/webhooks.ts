export interface WebhookType {
  id: string;
  name: string;
  description: string;
}

export interface Webhook {
  id: string;
  url: string;
  filter: string;
  include_last: boolean;
}

export const webhookTypes: WebhookType[] = [
  {
    id: "app_request",
    name: "App Request",
    description:
      "This is called when a request is received by the OpenGlück app server.",
  },
  {
    id: "userdata:set",
    name: "User Data Set",
    description: "This is called when an userdata has been set.",
  },
  {
    id: "userdata:lpush",
    name: "User Data Lpush",
    description:
      "This is called when an userdata has been pushed to the front.",
  },
  {
    id: "glucose:changed",
    name: "Glucose Measurement Changed",
    description:
      "This is called when new records are received. This webhook received both the previous and new current records.",
  },
  {
    id: "instant-glucose:changed",
    name: "Instant Glucose Measurement Changed",
    description:
      "This is called when new instant glucose records are received. This webhook received both the previous and new current records.",
  },
  {
    id: "instant-glucose:new",
    name: "New Instant Glucose Measurement",
    description:
      "This is called every time a new instant glucose measurement is received. Includes the last low record as context.",
  },
  {
    id: "episode:changed",
    name: "Glucose Episode Changed",
    description:
      "This is called when new episodes are received. This webhook received both the previous and new current records.",
  },
  {
    id: "glucose:new:historic",
    name: "New Historic Glucose Measurement",
    description:
      "This is called when a new historic glucose measurement is received.",
  },
  {
    id: "glucose:new:scan",
    name: "New Scan Glucose Measurement",
    description:
      "This is called when a new scan glucose measurement is received.",
  },
  {
    id: "low:changed",
    name: "Low Changed",
    description:
      "This is called when a low record is added, updated, or deleted.",
  },
  {
    id: "insulin:changed",
    name: "Insulin Changed",
    description:
      "This is called when an insulin record is added, updated, or deleted.",
  },
  {
    id: "food:changed",
    name: "Food Changed",
    description:
      "This is called when a food record is added, updated, or deleted.",
  },
];
