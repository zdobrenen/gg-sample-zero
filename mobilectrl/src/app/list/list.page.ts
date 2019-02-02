import { Component, OnInit, Input } from '@angular/core';
import { ModalController, Events } from '@ionic/angular';

import { ListItemModal } from './list.item.modal';
import { DeviceItem, DeviceList } from '../classes/item.class';

import { API } from "aws-amplify";


@Component({
  selector: 'app-list-page',
  templateUrl: 'list.page.html',
  styleUrls: ['list.page.scss']
})
export class ListPage implements OnInit {

    modal: any;
    data: any;
    user: any;
    deviceList: DeviceList;
    signedIn: boolean;


    constructor(
        public modalController: ModalController,
        events: Events

    ) {

        // Listen for changes to the AuthState in order to change item list appropriately
        events.subscribe('data:AuthState', async (data) => {
            if (data.loggedIn){
                this.signedIn = data.loggedIn;
                this.getItems();
            } else {
                this.signedIn = data.loggedIn;
                this.deviceList.items = [];
            }
        })
    }


    async ngOnInit() {
        this.getItems();
    }


    modify(item, i) {

        let props = {
            deviceList: this.deviceList || new DeviceList({userId: this.user.id}),
            editItem: item || undefined
        };

        if (props.editItem) {
            let deviceId = props.editItem.thingName;
            let devicePayload = {
                running: !props.editItem.state.running
            }

            this.pushItem(deviceId, devicePayload).then(deviceResponse => {
                this.getItems();
            })
        }
    }

    async telemetry(item, i) {

        let props = await this.getTelemetry(item.thingName);

        console.log(props);

        // Create the modal
        this.modal = await this.modalController.create({
            component: ListItemModal,
            componentProps: props
        });

        // Listen for the modal to be closed...
        this.modal.onDidDismiss((result) => {
            if (result.data.newItem){
                // ...and add a new item if modal passes back newItem
                result.data.deviceList.items.push(result.data.newItem)
            } else if (result.data.editItem){
            // ...or splice the items array if the modal passes back editItem
                result.data.deviceList.items[i] = result.data.editItem
            }
        })
        return this.modal.present()
    }



    getItems() {
        let deviceArray = [
            'GG_BTN_BLUE',
            'GG_BTN_YELLOW'
        ];

        this.deviceList = {userId: 1, items: []}
        for (let deviceId of deviceArray) {

            this.loadItem(deviceId).then(deviceResponse => {

                let deviceItem = new DeviceItem({
                    thingName: deviceId,
                    state: JSON.parse(deviceResponse).state.reported
                });

                this.deviceList.items.push(deviceItem);
            })

        }
    }

    getTelemetry(deviceId) {
        return this.loadTelemetry(deviceId).then(deviceResponse => {

           let telem_current_active = deviceResponse.records.map(i => {
                return {x: i.time, y: i.current_active};
            }).reverse();

            let telem_total_active   = deviceResponse.records.map(i => {
                return {x: i.time, y: i.total_active};
            }).reverse();

            let telem_current_inactive = deviceResponse.records.map(i => {
                return {x: i.time, y: i.current_inactive};
            }).reverse();

            let telem_total_inactive = deviceResponse.records.map(i => {
                return {x: i.time, y: i.total_inactive};
            }).reverse();

            return {
                telem_current_active: telem_current_active,
                telem_current_inactive: telem_current_inactive,
                telem_total_active: telem_total_active,
                telem_total_inactive: telem_total_inactive
            }
        })
    }


    async loadItem(id) {
        let apiName = 'iotShadowAPIGet';
        let path = '/shadow/' + id;
        let payload = {};

        return await API.get(apiName, path, payload);
    }


    async pushItem(id, updates) {
        let apiName = 'iotShadowAPIPost';
        let path = '/shadow/update/' + id;
        let payload = {
            body: updates
        };

        return await API.post(apiName, path, payload);
    }


    async loadTelemetry(id) {
        let apiName = 'iotTelemetryAPIGet';
        let path = '/telemetry/' + id;
        let payload = {};

        return await API.get(apiName, path, payload);
    }
}
