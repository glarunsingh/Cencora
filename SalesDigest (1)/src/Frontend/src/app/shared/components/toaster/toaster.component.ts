import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-toaster',
  templateUrl: './toaster.component.html',
  styleUrls: ['./toaster.component.scss']
})
export class ToasterComponent {

  @Input() title!: string;
  @Input() message!: string;
  @Input() infoColor!:string;

  ngPnInit() { 

  }

}
