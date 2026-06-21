import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosConfig";



const CategoriesList = () => {

    const [categories, setCategories] = useState([]);

    useEffect(() => {
        // Simulate fetching categories from an API
       
        axiosInstance
        .get('/finances/categories/')
        .then(res => {
            setCategories(res.data);
        })
        .catch(console.error)
        .finally(() => {
            // You can set a loading state here if needed
        });  
           
    }, []);

  return (
    <div className="dashboard-card--large">
        <h2>Categories List</h2>
      <ul>
        {categories.length === 0 ? (
          <li>Loading categories...</li>
        ) : (
          categories.map((category, index) => (
            <li className="tx-filter-select" style={{
                                                    color: category?.color ?? '#888',
                                                    background: (category?.color ?? '#888') + '1a',
                                                    border: `1px solid ${(category?.color ?? '#888')}80` }} key={index}>{category.name}</li>
          ))
        )}
      </ul>
     
    </div>
  );
}

export default CategoriesList;