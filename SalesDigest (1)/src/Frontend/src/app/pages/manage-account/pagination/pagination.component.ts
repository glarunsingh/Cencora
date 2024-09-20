import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-pagination',
  templateUrl: './pagination.component.html',
  styleUrls: ['./pagination.component.scss']
})
export class PaginationComponent {

  @Output() emitPageNumber = new EventEmitter();


  @Output() emitPaginatedRecords = new EventEmitter();
  @Input() tableRecords!: any[];
  @Input() currentPage!: number;
  //pagination
  recordsPerPage: number = 10;

  totalPages: number | any;

  pagesToShow = 5; // Number of pages to show in pagination
  pageNumbers: number[] = []; // Array to hold page numbers
  //pagination

  constructor() { }

  ngOnInit() {
    this.generatePagination()
  }

  ngOnChanges() {
    this.generatePagination()
  }

  /**pagination logic */

  generatePagination(): void {
    const totalRecLen = this.tableRecords?.length
    const totalPages = Math.ceil(totalRecLen / this.recordsPerPage);
    if (totalPages > this.currentPage + 4) {
      // const startPage = Math.max(1, this.currentPage - Math.floor(this.pagesToShow / 2));
      // const endPage = Math.min(totalPages, startPage + this.pagesToShow - 1);
      const startPage = this.currentPage - 2 < 0 ? 0 : this.currentPage - 2;
      const endPage = this.currentPage + 2 < 5 ? 5 : this.currentPage + 2;
      this.pageNumbers = [];
      for (let i = startPage; i <= endPage; i++) {
        this.pageNumbers.push(i + 1);
      }
      this.emitPageNumber.emit(this.currentPage)
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.generatePagination();
    }
  }

  nextPage(): void {
    // const totalPages = Math.ceil(this.tableRecords?.length / this.recordsPerPage);
    // if (this.currentPage < totalPages) {
    //   this.currentPage++;
    //   this.generatePagination();
    // }

    this.currentPage++;
    this.generatePagination();
  }

  goToPage(pageNumber: number): void {
    this.currentPage = pageNumber;
    this.generatePagination();
  }

  /**pagination logic */

  ngOnDestroy() {
    this.tableRecords = [];
  }

}
