import { v4 as uuid } from 'uuid';

export class DeviceList {
    userId: any;
    items: Array<DeviceItem>

    constructor(params){
        this.items = params.items || [];
        this.userId = params.userId;
  }
}


export class DeviceItem {
    thingName: string;
    state: any;

    constructor(params){
        this.thingName = params.thingName,
        this.state = params.state
    }
}
