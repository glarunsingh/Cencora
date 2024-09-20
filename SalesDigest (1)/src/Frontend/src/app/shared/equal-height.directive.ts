import { Directive, ElementRef } from '@angular/core';

@Directive({
  selector: '[appEqualHeight]'
})
export class EqualHeightDirective {

  // constructor(public el: ElementRef) { }

  // ngAfterViewInit() {
  //   this.setFixedHeight();
  // }

  // setFixedHeight() {
  //   const cardElements = this.el.nativeElement.querySelectorAll('.card');
  //   if (cardElements.lenght) {
  //     cardElements.forEach((card: HTMLElement) => {
  //       card['style']['height'] = '173px';
  //     });
  //   }
  // }

}
