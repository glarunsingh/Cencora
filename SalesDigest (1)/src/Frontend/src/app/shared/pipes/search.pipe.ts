import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'search'
})
export class SearchPipe implements PipeTransform {

  transform(list: any[], searchText: string, key?: any): any[] {
    if (!list) { return []; }
    if (!searchText) { return list; }

    searchText = searchText.toLowerCase();
    return list.filter(item => {
      // if (item?.text) return item.text.toLowerCase().includes(searchText);
      // return item.toLowerCase().includes(searchText);
      return JSON.stringify(item).toLowerCase().includes(searchText);
    });
  }

}
