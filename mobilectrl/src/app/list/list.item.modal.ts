import { Component, OnInit, ViewChild} from '@angular/core';
import { ModalController } from '@ionic/angular';
import { DeviceItem, DeviceList } from '../classes/item.class';
import { Chart } from 'chart.js';

import { API } from "aws-amplify";


@Component({
    selector: 'item-modal',
    templateUrl: 'list.item.modal.html',
})
export class ListItemModal implements OnInit {


    telem_current_active: any;
    telem_total_active: any;
    telem_current_inactive: any;
    telem_total_inactive: any;

    @ViewChild('curActiveCanvas') curActiveCanvas;
    @ViewChild('curInactiveCanvas') curInactiveCanvas;
    @ViewChild('totActiveCanvas') totActiveCanvas;
    @ViewChild('totInactiveCanvas') totInactiveCanvas;

    curActiveChart: any;
    curInactiveChart: any;

    totActiveChart: any;
    totInactiveChart: any;

    constructor(private modalController: ModalController) {}


    ngOnInit(){

        this.curActiveChart = new Chart(this.curActiveCanvas.nativeElement, {

            type: 'line',
            data: {
                datasets: [
                    {
                        label: "Current Activity",
                        fill: false,
                        lineTension: 0.1,
                        backgroundColor: "rgba(75,192,192,0.4)",
                        borderColor: "rgba(75,192,192,1)",
                        borderCapStyle: 'butt',
                        borderDash: [],
                        borderDashOffset: 0.0,
                        borderJoinStyle: 'miter',
                        pointBorderColor: "rgba(75,192,192,1)",
                        pointBackgroundColor: "#fff",
                        pointBorderWidth: 1,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: "rgba(75,192,192,1)",
                        pointHoverBorderColor: "rgba(220,220,220,1)",
                        pointHoverBorderWidth: 2,
                        pointRadius: 1,
                        pointHitRadius: 10,
                        data: this.telem_current_active,
                        spanGaps: false,
                    }
                ]
            },
            options: {
                responsive: true,
                title:      {
                    display: true,
                    text:    "Current Activity"
                },
                scales:     {
                    xAxes: [{
                        type: "time",
                        time: {
                            unit: 'second'
                        },
                        scaleLabel: {
                            display:     true,
                            labelString: 'Timestamp (UTC)'
                        },
                        ticks: {
                            maxRotation: 90,
                            source: 'data'
                        }
                    }],
                    yAxes: [{
                        scaleLabel: {
                            display:     true,
                            labelString: 'Activity (seconds)'
                        }
                    }]
                }
            }
        });

        this.curInactiveChart = new Chart(this.curInactiveCanvas.nativeElement, {

            type: 'line',
            data: {
                datasets: [
                    {
                        label: "Current Inactivity",
                        fill: false,
                        lineTension: 0.1,
                        backgroundColor: "rgba(75,192,192,0.4)",
                        borderColor: "rgba(75,192,192,1)",
                        borderCapStyle: 'butt',
                        borderDash: [],
                        borderDashOffset: 0.0,
                        borderJoinStyle: 'miter',
                        pointBorderColor: "rgba(75,192,192,1)",
                        pointBackgroundColor: "#fff",
                        pointBorderWidth: 1,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: "rgba(75,192,192,1)",
                        pointHoverBorderColor: "rgba(220,220,220,1)",
                        pointHoverBorderWidth: 2,
                        pointRadius: 1,
                        pointHitRadius: 10,
                        data: this.telem_current_inactive,
                        spanGaps: false,
                    }
                ]
            },
            options: {
                responsive: true,
                title:      {
                    display: true,
                    text:    "Current Inactivity"
                },
                scales:     {
                    xAxes: [{
                        type: "time",
                        time: {
                            unit: 'second'
                        },
                        scaleLabel: {
                            display:     true,
                            labelString: 'Timestamp (UTC)'
                        },
                        ticks: {
                            maxRotation: 90,
                            source: 'data'
                        }
                    }],
                    yAxes: [{
                        scaleLabel: {
                            display: true,
                            labelString: 'Inactivity (seconds)'
                        }
                    }]
                }
            }
        });

        this.totActiveChart = new Chart(this.totActiveCanvas.nativeElement, {

            type: 'line',
            data: {
                datasets: [
                    {
                        label: "Total Activity",
                        fill: false,
                        lineTension: 0.1,
                        backgroundColor: "rgba(75,192,192,0.4)",
                        borderColor: "rgba(75,192,192,1)",
                        borderCapStyle: 'butt',
                        borderDash: [],
                        borderDashOffset: 0.0,
                        borderJoinStyle: 'miter',
                        pointBorderColor: "rgba(75,192,192,1)",
                        pointBackgroundColor: "#fff",
                        pointBorderWidth: 1,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: "rgba(75,192,192,1)",
                        pointHoverBorderColor: "rgba(220,220,220,1)",
                        pointHoverBorderWidth: 2,
                        pointRadius: 1,
                        pointHitRadius: 10,
                        data: this.telem_total_active,
                        spanGaps: false,
                    }
                ]
            },
            options: {
                responsive: true,
                title:      {
                    display: true,
                    text:    "Total Activity"
                },
                scales:     {
                    xAxes: [{
                        type: "time",
                        time: {
                            unit: 'second'
                        },
                        scaleLabel: {
                            display:     true,
                            labelString: 'Timestamp (UTC)'
                        },
                        ticks: {
                            maxRotation: 90,
                            source: 'data'
                        }
                    }],
                    yAxes: [{
                        scaleLabel: {
                            display:     true,
                            labelString: 'Activity (seconds)'
                        }
                    }]
                }
            }
        });

        this.totInactiveChart = new Chart(this.totInactiveCanvas.nativeElement, {

            type: 'line',
            data: {
                datasets: [
                    {
                        label: "Total Inactivity",
                        fill: false,
                        lineTension: 0.1,
                        backgroundColor: "rgba(75,192,192,0.4)",
                        borderColor: "rgba(75,192,192,1)",
                        borderCapStyle: 'butt',
                        borderDash: [],
                        borderDashOffset: 0.0,
                        borderJoinStyle: 'miter',
                        pointBorderColor: "rgba(75,192,192,1)",
                        pointBackgroundColor: "#fff",
                        pointBorderWidth: 1,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: "rgba(75,192,192,1)",
                        pointHoverBorderColor: "rgba(220,220,220,1)",
                        pointHoverBorderWidth: 2,
                        pointRadius: 1,
                        pointHitRadius: 10,
                        data: this.telem_total_inactive,
                        spanGaps: false,
                    }
                ]
            },
            options: {
                responsive: true,
                title:      {
                    display: true,
                    text:    "Total Inactivity"
                },
                scales:     {
                    xAxes: [{
                        type: "time",
                        time: {
                            unit: 'second'
                        },
                        scaleLabel: {
                            display:     true,
                            labelString: 'Timestamp (UTC)'
                        },
                        ticks: {
                            maxRotation: 90,
                            source: 'data'
                        }
                    }],
                    yAxes: [{
                        scaleLabel: {
                            display:     true,
                            labelString: 'Inactivity (seconds)'
                        }
                    }]
                }
            }
        });
    }

    close() {
        this.modalController.dismiss()
    }
}
