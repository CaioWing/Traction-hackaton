import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import ServiceBox from '../components/ServiceBox';
import { styled } from 'styled-components';

interface ManutencaoMaquina {
  _id: string;
  problema: string;
  solucao: {
    passos: Passo[];
    equipamentos_necessarios: string[];
    observacoes: string[];
    referencias: string[];
  };
}

interface Passo {
  ordem: number;
  descricao: string;
  justificativa: string;
  medidas_seguranca: string[];
}

const LinkDecor = styled.a`
  text-decoration: none;
  color: inherit;
`;

function ServicesList() {
  const [data, setdata] = useState<ManutencaoMaquina[]>([]);
  useEffect(() => {
    const fetchData = async () => {
      const data = await fetch('http://localhost:8000/getServices');
      const datajs = await data.json();
      setdata(datajs);
      console.log(datajs);
    };

    // call the function
    fetchData()
      // make sure to catch any error
      .catch(console.error);
  }, []);

  return (
    <>
      <Header></Header>
      {data?.map((service) => (
        <LinkDecor href={`/service/${service._id}`}>
          <ServiceBox title={service.problema}>
            {service.solucao.equipamentos_necessarios.map((tool) => (
              <p>{tool}</p>
            ))}
          </ServiceBox>
        </LinkDecor>
      ))}
    </>
  );
}

export default ServicesList;
