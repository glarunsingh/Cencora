import { ChangeDetectorRef, Component, EventEmitter, Input, Output, SimpleChanges } from '@angular/core';

interface FiltersObj {
  total: number;
  name: string;
}

@Component({
  selector: 'app-filters-count',
  templateUrl: './filters-count.component.html',
  styleUrls: ['./filters-count.component.scss']
})
export class FiltersCountComponent {
  @Output() clearAllFilters = new EventEmitter();
  @Input() inputfiltersObj!: FiltersObj;
  public filtersObj!: FiltersObj;

  constructor() { }

  ngOnInit() {
    console.log("this.inputfiltersObj", this.inputfiltersObj)
    this.filtersObj = JSON.parse(JSON.stringify(this.inputfiltersObj))
  }

  ngOnChanges(changes:SimpleChanges) {
    console.log("this.inputfiltersObj", this.inputfiltersObj)
    this.filtersObj = JSON.parse(JSON.stringify(this.inputfiltersObj))
  }

  clearAllSelectedFilter(filterName: string) {
    this.clearAllFilters.emit(filterName)
  }

}
