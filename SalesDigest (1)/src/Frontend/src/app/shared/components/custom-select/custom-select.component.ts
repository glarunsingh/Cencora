import { Component, EventEmitter, HostListener, Input, Output } from '@angular/core';

@Component({
  selector: 'app-custom-select',
  templateUrl: './custom-select.component.html',
  styleUrls: ['./custom-select.component.scss']
})
export class CustomSelectComponent {

  @Output() emitSelectedItem = new EventEmitter();
  @Input() options!: string[];
  @Input() placeholder: any;
  selectedOption: string | null = null;
  dropdownOpen = false;

  toggleDropdown() {
    this.dropdownOpen = !this.dropdownOpen;
  }

  selectOption(option: string, event: any) {
    event.stopPropagation();
    this.selectedOption = option;
    this.dropdownOpen = false;
    this.emitSelectedItem.emit(option)
  }

  @HostListener('document:click', ['$event'])
  closeDropdown(event: Event) {
    const target = event.target as HTMLElement;
    if (!target.closest('.custom-select')) {
      this.dropdownOpen = false;
    }
  }

}
